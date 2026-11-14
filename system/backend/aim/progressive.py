"""Reusable progressive replay runner, shared by CLI and controlled API jobs."""

from __future__ import annotations

import math
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

import httpx

from .dataset import SERIES, DatasetCut, case_directory, file_record, load_cut, load_ground_truth
from .replay import send_replay, verify_persisted
from .repository import Repository
from .transform import BUCKET_NANOSECONDS_60S, CADENCE, METRICS, NANO, run_transform, run_transform_60s


def _send_slice(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Short transient retries send the identical idempotent OTLP source slice."""
    for attempt in range(4):
        try:
            return send_replay(*args, **kwargs)
        except httpx.HTTPStatusError as error:
            if error.response.status_code not in {429, 502, 503, 504} or attempt == 3:
                raise
        except httpx.TransportError:
            if attempt == 3:
                raise
        time.sleep(0.25 * (2 ** attempt))
    raise RuntimeError("Unreachable retry state")


def _source_signature(root: Path) -> tuple:
    base = case_directory(root)
    return tuple((relative, (base / relative).stat().st_size, (base / relative).stat().st_mtime_ns)
                 for relative in [*(spec.relative_path for spec in SERIES), "groundtruth/groundtruth.json"])


@lru_cache(maxsize=2)
def _cached_cut(root: str, signature: tuple) -> DatasetCut:
    cut = load_cut(Path(root))
    if _source_signature(Path(root)) != signature:
        raise ValueError("Source files changed while the replay cut was being validated")
    return cut


def run_progressive(
    dataset_root: Path,
    api_url: str,
    *,
    cut: DatasetCut | None = None,
    metrics_endpoint: str | None = None,
    chunk_timestamps: int = 8,
    pause_seconds: float = 3.0,
    initial_pause_seconds: float = 3.0,
    transform_every_chunks: int = 1,
    include_ground_truth: bool = False,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if chunk_timestamps < 3 or transform_every_chunks < 1:
        raise ValueError("Progressive replay needs at least three timestamps and one transform milestone")
    if not all(math.isfinite(pause) and pause >= 0 for pause in (pause_seconds, initial_pause_seconds)):
        raise ValueError("Progressive replay pauses must be finite and nonnegative")
    notify = on_progress or (lambda update: None)
    notify({"current_stage": "loading_source"})
    # Cache only 282 original source values and hashes in memory. A changed file
    # size or mtime invalidates it; no CSV copy or precomputed feature is stored.
    cut = cut or _cached_cut(str(dataset_root.resolve()), _source_signature(dataset_root))
    point_count = len(cut.series[0].points)
    chunk_count = math.ceil(point_count / chunk_timestamps)
    expected_points = sum(len(series.points) for series in cut.series)
    with httpx.Client(timeout=30, trust_env=False) as client:
        created = client.post(f"{api_url.rstrip('/')}/api/v1/replays", json=cut.replay_payload())
        created.raise_for_status()
        replay_id = created.json()["replay_run_id"]
    notify({"replay_run_id": replay_id, "current_stage": "sending", "total_chunks": chunk_count,
            "completed_chunks": 0, "raw_point_count": 0, "expected_raw_point_count": expected_points})
    repository = Repository()
    chunks = []
    final_transform = final_transform_60s = final_verification = None
    last_60s_watermark = None
    display_start = int(cut.replay_payload()["display_start_unix_nano"])
    for number, start in enumerate(range(0, point_count, chunk_timestamps), 1):
        stop = min(start + chunk_timestamps, point_count)
        sent = _send_slice(cut, api_url, replay_id, start, stop, metrics_endpoint=metrics_endpoint)
        # A Collector receipt alone is not proof of AIM's commit. Poll the actual
        # PostgreSQL input before announcing progress or running a transformation.
        deadline = time.monotonic() + 60
        while True:
            persisted = repository.get_raw_points(replay_id)
            if len(persisted) >= stop * len(cut.series):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError("Collector export did not reach PostgreSQL before the deadline")
            time.sleep(0.1)
        watermark = max(int(point["time_unix_nano"]) for point in persisted)
        update: dict[str, Any] = {"replay_run_id": replay_id, "current_stage": "transforming",
            "completed_chunks": number, "total_chunks": chunk_count, "raw_point_count": len(persisted),
            "expected_raw_point_count": expected_points, "watermark_unix_nano": str(watermark)}
        notify(update)
        chunk = {"chunk_number": number, "chunk_count": chunk_count, "source_point_count": sent["source_point_count"],
                 "source_time_start_unix_nano": str(sent["source_time_start_unix_nano"]),
                 "source_time_end_unix_nano": str(sent["source_time_end_unix_nano"]), "replay_run_id": replay_id}
        if number == chunk_count or number % transform_every_chunks == 0:
            end_60s = display_start + ((watermark - display_start) // BUCKET_NANOSECONDS_60S) * BUCKET_NANOSECONDS_60S
            if end_60s > display_start and end_60s != last_60s_watermark:
                final_transform_60s = run_transform_60s(repository, replay_id, until_unix_nano=watermark)
                last_60s_watermark = end_60s
                chunk.update(transform_60s_run_id=final_transform_60s["transform_run_id"], transform_60s_summary=final_transform_60s["summary"])
                update["latest_transform_60s_run_id"] = final_transform_60s["transform_run_id"]
            final_transform = run_transform(repository, replay_id, until_unix_nano=watermark)
            chunk.update(transform_run_id=final_transform["transform_run_id"], transform_summary=final_transform["summary"])
            update["latest_transform_run_id"] = final_transform["transform_run_id"]
        chunks.append(chunk)
        update["current_stage"] = "waiting" if number < chunk_count else "verifying"
        notify(update)
        if number < chunk_count:
            time.sleep(initial_pause_seconds if number == 1 else pause_seconds)
    notify({"current_stage": "verifying_source"})
    base = case_directory(dataset_root)
    for source_file in cut.source_manifest["files"]:
        actual = file_record(base / source_file["relative_path"], source_file["relative_path"], source_file["role"])
        if actual["sha256"] != source_file["sha256"]:
            raise ValueError("Source content changed from the manifest used for this demonstration")
    final_verification = verify_persisted(cut, repository.get_raw_points(replay_id))
    if final_transform is None or final_transform_60s is None:
        raise RuntimeError("Both final persisted transform resolutions are required")
    expected_windows = (int(cut.replay_payload()["display_end_unix_nano"]) - display_start) // (CADENCE * NANO)
    expected_60s = (int(cut.replay_payload()["display_end_unix_nano"]) - display_start) // BUCKET_NANOSECONDS_60S
    summary, summary_60s = final_transform["summary"], final_transform_60s["summary"]
    positive = {metric: summary_60s["metrics"][metric]["positive_value_count"] for metric in METRICS}
    if final_verification["verified_points"] != expected_points or summary["visible_windows"] != expected_windows or summary["coverage_rows"] != expected_windows * len(METRICS):
        raise RuntimeError("The final faithful transform does not match the audited source cut")
    if summary_60s["visible_windows"] != expected_60s or summary_60s["numeric_derived_points"] != expected_60s * len(METRICS):
        raise RuntimeError("The final 60-second transform does not cover the expected complete buckets")
    if positive != {"cpu_cores": 17, "success_response_rate": 23, "success_latency_mean_ms": 23}:
        raise RuntimeError("The final aggregate positive-value counts differ from the audited cut")
    if include_ground_truth:
        notify({"current_stage": "importing_ground_truth"})
        digest, events = load_ground_truth(dataset_root)
        expected = next(file["sha256"] for file in cut.source_manifest["files"] if file["role"] == "ground_truth")
        if digest != expected:
            raise ValueError("Ground truth source differs from the registered replay manifest")
        repository.import_ground_truth(replay_id, events)
    return {"stage": "progressive_historical_replay", "status": "complete", "replay_run_id": replay_id,
        "transport": "OTLP/HTTP Protobuf through the configured API/Collector path", "source_point_count": expected_points,
        "chunk_count": chunk_count, "chunk_timestamps": chunk_timestamps, "pause_seconds": pause_seconds,
        "initial_pause_seconds": initial_pause_seconds, "verification": final_verification,
        "final_transform": final_transform, "final_transform_60s": final_transform_60s,
        "expected_full_result": {"faithful_15s": {"visible_windows": expected_windows, "coverage_rows": summary["coverage_rows"], "numeric_derived_points": summary["numeric_derived_points"]},
            "aggregated_60s": {"visible_windows": expected_60s, "coverage_rows": summary_60s["coverage_rows"], "numeric_derived_points": summary_60s["numeric_derived_points"], "positive_value_counts": positive}},
        "chunks": chunks, "interpretation": "Historical replay progress, not live telemetry or a validated detector."}
