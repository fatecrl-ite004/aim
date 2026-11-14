"""Streaming adapter for the explicitly selected, external AIOpsArena cut.

Only sampled source counters are read here. Rates and latency belong to the
post-persistence transform, never to this adapter or the replayer.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

NANO = 1_000_000_000
SOURCE_START = 1_719_205_965
DISPLAY_START = 1_719_205_980
DISPLAY_END = 1_719_207_360
CADENCE = 15
SERVICE = "recommendationservice"
INSTANCE = "recommendationservice-1"
REPLAYER_VERSION = "aiopsarena-v1"
MAPPING_VERSION = "recommendationservice-v1"


@dataclass(frozen=True)
class SeriesSpec:
    role: str
    relative_path: str
    cmdb_id: str
    metric_name: str
    unit: str


SERIES = (
    SeriesSpec(
        "cpu",
        "metric/container/kpi_container_cpu_usage_seconds_total.csv",
        "observe.recommendationservice-1",
        "container_cpu_usage_seconds_total",
        "s",
    ),
    SeriesSpec(
        "requests",
        "metric/istio/kpi_istio_requests_total.csv",
        "recommendationservice-1.destination.frontend.recommendationservice",
        "istio_requests_total.grpc.200.0",
        "1",
    ),
    SeriesSpec(
        "duration",
        "metric/istio/kpi_istio_request_duration_milliseconds_sum.csv",
        "recommendationservice-1.destination.frontend.recommendationservice",
        "istio_request_duration_milliseconds_sum.grpc.200.0",
        "ms",
    ),
)


@dataclass(frozen=True)
class SourcePoint:
    timestamp: int
    value: float
    row_ordinal: int


@dataclass(frozen=True)
class SourceSeries:
    spec: SeriesSpec
    file_sha256: str
    points: tuple[SourcePoint, ...]


@dataclass(frozen=True)
class DatasetCut:
    source_manifest: dict[str, Any]
    series: tuple[SourceSeries, ...]

    def replay_payload(self) -> dict[str, Any]:
        return {
            "dataset": "aiopsarena",
            "dataset_case": "Case-1",
            "service_name": SERVICE,
            "instance_id": INSTANCE,
            "display_start_unix_nano": str(DISPLAY_START * NANO),
            "display_end_unix_nano": str(DISPLAY_END * NANO),
            "raw_start_unix_nano": str(SOURCE_START * NANO),
            "raw_end_unix_nano": str(DISPLAY_END * NANO),
            "source_manifest": self.source_manifest,
            "replayer_version": REPLAYER_VERSION,
            "mapping_version": MAPPING_VERSION,
        }


def case_directory(dataset_root: Path) -> Path:
    base = dataset_root.expanduser().resolve() / "Case-1" / "Case-1"
    if not base.is_dir():
        raise FileNotFoundError(f"Expected external AIOpsArena Case-1/Case-1 under {dataset_root}")
    return base


def file_record(path: Path, relative_path: str, role: str) -> dict[str, Any]:
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    return {"role": role, "relative_path": relative_path, "sha256": digest, "size_bytes": path.stat().st_size}


def load_cut(dataset_root: Path) -> DatasetCut:
    """Read CSVs with bounded memory; keep original timestamps and global ordinals."""
    base = case_directory(dataset_root)
    source_series = []
    files = []
    expected_timestamps = list(range(SOURCE_START, DISPLAY_END + CADENCE, CADENCE))
    for spec in SERIES:
        path = base / spec.relative_path
        record = file_record(path, spec.relative_path, spec.role)
        files.append(record)
        points = []
        with path.open(newline="", encoding="utf-8-sig", buffering=4 * 1024 * 1024) as source:
            reader = csv.reader(source)
            header = next(reader, [])
            if not {"timestamp", "cmdb_id", "kpi_name", "value"}.issubset(header):
                raise ValueError(f"Unexpected CSV header for {spec.relative_path}")
            columns = {name: header.index(name) for name in ("timestamp", "cmdb_id", "kpi_name", "value")}
            for ordinal, row in enumerate((record for record in reader if record), 1):
                if len(row) < len(header):
                    raise ValueError(f"Incomplete CSV row at {spec.relative_path}:{ordinal}")
                # Filter identity before parsing unrelated source values.
                if row[columns["cmdb_id"]] != spec.cmdb_id or row[columns["kpi_name"]] != spec.metric_name:
                    continue
                timestamp = int(row[columns["timestamp"]])
                if not SOURCE_START <= timestamp <= DISPLAY_END:
                    continue
                value = float(row[columns["value"]])
                if not math.isfinite(value) or value < 0:
                    raise ValueError(f"Invalid source counter at {spec.relative_path}:{ordinal}")
                points.append(SourcePoint(timestamp, value, ordinal))
        points.sort(key=lambda point: (point.timestamp, point.row_ordinal))
        if [point.timestamp for point in points] != expected_timestamps:
            raise ValueError(f"Source cut changed: expected exactly 94 distinct points at 15s in {spec.relative_path}")
        source_series.append(SourceSeries(spec, record["sha256"], tuple(points)))
    relative = "groundtruth/groundtruth.json"
    files.append(file_record(base / relative, relative, "ground_truth"))
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    manifest = {"files": files, "manifest_sha256": hashlib.sha256(canonical).hexdigest()}
    return DatasetCut(manifest, tuple(source_series))


def load_ground_truth(dataset_root: Path) -> tuple[str, list[dict[str, Any]]]:
    """A separate operation: labels never become metric datapoints."""
    base = case_directory(dataset_root)
    relative = "groundtruth/groundtruth.json"
    path = base / relative
    record = file_record(path, relative, "ground_truth")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    columns = ("timestamp", "service", "cmdb_id", "failure_type", "duration")
    if not isinstance(data, dict) or any(not isinstance(data.get(key), list) for key in columns):
        raise ValueError("Expected ground truth column arrays")
    if len({len(data[key]) for key in columns}) != 1:
        raise ValueError("Ground truth columns have different lengths")
    selected = []
    for index in range(len(data["timestamp"])):
        if data["cmdb_id"][index] != INSTANCE:
            continue
        start = int(data["timestamp"][index])
        duration = int(data["duration"][index])
        if start != 1_719_206_280 or duration != 780 or data["failure_type"][index] != "cpu":
            raise ValueError("Selected ground truth event differs from the documented engineering cut")
        selected.append({
            "service_name": SERVICE,
            "instance_id": INSTANCE,
            "start_unix_nano": start * NANO,
            "end_unix_nano": (start + duration) * NANO,
            "failure_type": "cpu",
            "event_type": "injected_fault",
            "source_file_sha256": record["sha256"],
            "source_event_ordinal": index + 1,
        })
    if len(selected) != 1:
        raise ValueError("Expected exactly one selected injected CPU event")
    return record["sha256"], selected


def audit_cut(cut: DatasetCut) -> dict[str, Any]:
    """Metadata only: suitable for versioned evidence without copying the source."""
    return {
        "dataset": "aiopsarena", "dataset_case": "Case-1",
        "service_name": SERVICE, "instance_id": INSTANCE,
        "display_start_unix_nano": str(DISPLAY_START * NANO),
        "display_end_unix_nano": str(DISPLAY_END * NANO),
        "source_manifest": cut.source_manifest,
        "series": [{
            "metric_name": series.spec.metric_name, "source_cmdb_id": series.spec.cmdb_id,
            "unit": series.spec.unit, "point_count": len(series.points),
            "first_timestamp": series.points[0].timestamp,
            "last_timestamp": series.points[-1].timestamp,
            "cadence_seconds": sorted({right.timestamp - left.timestamp for left, right in zip(series.points, series.points[1:])}),
            "negative_deltas": sum(right.value < left.value for left, right in zip(series.points, series.points[1:])),
            "zero_deltas": sum(right.value == left.value for left, right in zip(series.points, series.points[1:])),
        } for series in cut.series],
        "limits": ["historical_replay", "only_grpc_200_status", "no_error_rate_or_percentiles", "no_detector_or_causality", "source_files_not_redistributed"],
    }
