"""Explicit, versioned batch derivation over committed PostgreSQL raw points."""

from __future__ import annotations

import math
import json
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from .dataset import CADENCE, DISPLAY_END, DISPLAY_START, INSTANCE, NANO, SERVICE, SERIES

TRANSFORM_VERSION = "counter-rates-v1"
TRANSFORM_60S_VERSION = "counter-rates-60s-v1"
BUCKET_SECONDS_60S = 60
BUCKET_NANOSECONDS_60S = BUCKET_SECONDS_60S * NANO
METRICS = {
    "cpu_cores": ("cores", "delta(cpu_seconds)/delta(time_seconds)"),
    "success_response_rate": ("1/s", "delta(grpc.200.0_responses)/delta(time_seconds)"),
    "success_latency_mean_ms": ("ms", "delta(grpc.200.0_duration_ms)/delta(grpc.200.0_responses)"),
}


@dataclass(frozen=True)
class Delta:
    value: int | float | None
    state: str
    reason: str | None
    points: tuple[dict[str, Any], ...]


def _delta(points: list[dict[str, Any]], start: int, end: int) -> Delta:
    if not points:
        return Delta(None, "missing", "source_series_missing", ())
    if len({str(point["series_id"]) for point in points}) != 1:
        return Delta(None, "invalid", "ambiguous_source_series", ())
    selected = [point for point in points if int(point["time_unix_nano"]) in (start, end)]
    left = [point for point in selected if int(point["time_unix_nano"]) == start]
    right = [point for point in selected if int(point["time_unix_nano"]) == end]
    if len(left) > 1 or len(right) > 1:
        return Delta(None, "invalid", "duplicate_timestamp", tuple(selected))
    if not left or not right:
        return Delta(None, "partial" if selected else "missing", "missing_endpoint", tuple(selected))
    before, after = left[0], right[0]
    if (before["service_name"], before["instance_id"], before["source_cmdb_id"]) != (after["service_name"], after["instance_id"], after["source_cmdb_id"]):
        return Delta(None, "invalid", "source_identity_changed", tuple(selected))
    if before.get("start_time_unix_nano") != after.get("start_time_unix_nano"):
        return Delta(None, "invalid", "counter_start_changed", tuple(selected))
    values = (before["value"], after["value"])
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 for value in values):
        return Delta(None, "invalid", "non_finite_or_negative_counter", tuple(selected))
    delta = values[1] - values[0]
    if delta < 0:
        return Delta(None, "invalid", "counter_decreased", tuple(selected))
    if end <= start:
        return Delta(None, "invalid", "invalid_interval", tuple(selected))
    return Delta(delta, "complete", None, tuple(selected))


def _api_pair_identity(point: dict[str, Any]) -> str:
    """Shared semantic dimensions, excluding metric-specific name and provenance."""
    resources = {key: value for key, value in point.get("resource_attributes", {}).items() if key not in ("aim.source.file_sha256", "aim.replay.run_id")}
    attributes = {key: value for key, value in point.get("datapoint_attributes", {}).items() if key not in ("aim.source.row_ordinal", "aim.source.kpi_name")}
    identity = {
        "source_cmdb_id": point["source_cmdb_id"], "resource": resources,
        "scope": {"name": point.get("scope_name", ""), "version": point.get("scope_version", ""), "attributes": point.get("scope_attributes", {})},
        "datapoint_attributes": attributes,
    }
    return json.dumps(identity, sort_keys=True, separators=(",", ":"))


def _unavailable(*deltas: Delta) -> tuple[str, str | None]:
    for state in ("invalid", "missing", "partial"):
        for delta in deltas:
            if delta.state == state:
                return state, delta.reason
    return "complete", None


def derive_observations(
    raw_points: list[dict[str, Any]],
    *,
    start_unix_nano: int = DISPLAY_START * NANO,
    end_unix_nano: int = DISPLAY_END * NANO,
    service_name: str = SERVICE,
    instance_id: str = INSTANCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """No labels or source files enter the calculation; absence stays explicit."""
    cadence_ns = CADENCE * NANO
    if end_unix_nano <= start_unix_nano or (end_unix_nano - start_unix_nano) % cadence_ns:
        raise ValueError("Transform bounds must contain whole, positive 15-second intervals")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in raw_points:
        if point["service_name"] == service_name and point["instance_id"] == instance_id:
            grouped[point["metric_name"]].append(point)
    by_role = {spec.role: grouped[spec.metric_name] for spec in SERIES}
    rows = []
    for start in range(start_unix_nano, end_unix_nano, cadence_ns):
        end = start + cadence_ns
        cpu, requests, duration = (_delta(by_role[role], start, end) for role in ("cpu", "requests", "duration"))
        seconds = (end - start) / NANO
        rate_value = requests.value / seconds if requests.state == "complete" else None
        latency_state, latency_reason = _unavailable(requests, duration)
        latency_value = None
        if latency_state == "complete":
            request_ids = {_api_pair_identity(point) for point in requests.points}
            duration_ids = {_api_pair_identity(point) for point in duration.points}
            if request_ids != duration_ids:
                latency_state, latency_reason = "invalid", "api_identity_mismatch"
            elif requests.value == 0:
                latency_state, latency_reason = ("not_applicable", "no_observed_increment") if duration.value == 0 else ("invalid", "duration_without_responses")
            else:
                latency_value = duration.value / requests.value
        outputs = (
            ("cpu_cores", cpu.value / seconds if cpu.state == "complete" else None, cpu.state, cpu.reason, cpu.points),
            ("success_response_rate", rate_value, requests.state, "no_observed_increment" if requests.state == "complete" and requests.value == 0 else requests.reason, requests.points),
            ("success_latency_mean_ms", latency_value, latency_state, latency_reason, requests.points + duration.points),
        )
        for metric, value, state, reason, inputs in outputs:
            unit, formula = METRICS[metric]
            rows.append({
                "metric_name": metric, "service_name": service_name, "instance_id": instance_id,
                "window_start_unix_nano": start, "window_end_unix_nano": end,
                "value": value, "unit": unit, "coverage_state": state, "reason": reason,
                "source_raw_point_ids": [point["id"] for point in inputs],
                "provenance": {"source_series_ids": sorted({str(point["series_id"]) for point in inputs}), "formula": formula},
            })
    summary = {
        "input_raw_points": len(raw_points),
        "visible_start_unix_nano": str(start_unix_nano),
        "visible_end_unix_nano": str(end_unix_nano),
        "visible_windows": (end_unix_nano - start_unix_nano) // cadence_ns,
        "coverage_rows": len(rows),
        "numeric_derived_points": sum(row["value"] is not None for row in rows),
        "metrics": {
            metric: {
                "coverage": dict(Counter(row["coverage_state"] for row in rows if row["metric_name"] == metric)),
                "reasons": dict(Counter(row["reason"] for row in rows if row["metric_name"] == metric and row["reason"])),
            } for metric in METRICS
        },
    }
    return rows, summary


def run_transform(
    repository: Any,
    replay_run_id: str,
    until_unix_nano: int | None = None,
) -> dict[str, Any]:
    replay = repository.get_replay(replay_run_id)
    if replay is None:
        raise ValueError("Replay not found")
    persisted_points = repository.get_raw_points(replay_run_id)
    if not persisted_points:
        raise ValueError("Replay has no committed raw points; OTLP ingestion is required before batch")
    start = int(replay["display_start_unix_nano"])
    display_end = int(replay["display_end_unix_nano"])
    end = display_end if until_unix_nano is None else int(until_unix_nano)
    cadence_ns = CADENCE * NANO
    if end > display_end:
        raise ValueError("Transform watermark cannot exceed the replay display end")
    if end <= start or (end - start) % cadence_ns:
        raise ValueError("Transform watermark must end on a positive 15-second window boundary")
    raw_points = [point for point in persisted_points if int(point["time_unix_nano"]) <= end]
    if not raw_points:
        raise ValueError("No committed source points are available through this transform watermark")
    persisted_watermark = max(int(point["time_unix_nano"]) for point in persisted_points)
    if end > persisted_watermark:
        raise ValueError("Transform watermark exceeds the latest persisted source timestamp")
    config = {
        "window_seconds": CADENCE, "display_start_unix_nano": str(start), "display_end_unix_nano": str(end),
        "service_name": replay["service_name"], "instance_id": replay["instance_id"],
        "warmup_delta_displayed": False, "missing_policy": "no_imputation",
        "counter_decrease_policy": "invalid_no_delta", "input": "committed_postgresql_raw_points",
        "formulas": {metric: formula for metric, (_, formula) in METRICS.items()},
        "input_raw_point_ids": sorted(point["id"] for point in raw_points),
        "input_raw_point_count": len(raw_points),
        "input_snapshot_sha256": hashlib.sha256(json.dumps(raw_points, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
    }
    transform_run_id = repository.start_transform_run(replay_run_id, TRANSFORM_VERSION, config)
    try:
        rows, summary = derive_observations(
            raw_points, start_unix_nano=start, end_unix_nano=end,
            service_name=replay["service_name"], instance_id=replay["instance_id"],
        )
        repository.write_transform_results(transform_run_id, rows)
        repository.finish_transform_run(transform_run_id, status="complete", summary=summary)
    except Exception:
        # Avoid persisting connection strings or arbitrary library exception text.
        repository.finish_transform_run(transform_run_id, status="failed", error="transform_execution_failed")
        raise
    return {
        "replay_run_id": replay_run_id,
        "transform_run_id": str(transform_run_id),
        "version": TRANSFORM_VERSION,
        "status": "complete",
        "summary": summary,
    }


def derive_observations_60s(
    raw_points: list[dict[str, Any]],
    *,
    start_unix_nano: int = DISPLAY_START * NANO,
    end_unix_nano: int = DISPLAY_END * NANO,
    service_name: str = SERVICE,
    instance_id: str = INSTANCE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Aggregate four complete 15-second counter deltas into each 60-second bucket."""
    if end_unix_nano <= start_unix_nano or (end_unix_nano - start_unix_nano) % BUCKET_NANOSECONDS_60S:
        raise ValueError("60-second transform bounds must contain whole, positive buckets")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in raw_points:
        if point["service_name"] == service_name and point["instance_id"] == instance_id:
            grouped[point["metric_name"]].append(point)
    by_role = {spec.role: grouped[spec.metric_name] for spec in SERIES}
    rows: list[dict[str, Any]] = []
    formula_by_metric = {
        "cpu_cores": "sum(four delta(cpu_seconds))/60",
        "success_response_rate": "sum(four delta(grpc.200.0_responses))/60",
        "success_latency_mean_ms": "sum(four delta(grpc.200.0_duration_ms))/sum(four delta(grpc.200.0_responses))",
    }

    def point_ids(deltas: tuple[Delta, ...] | list[Delta]) -> list[int]:
        return sorted({int(point["id"]) for delta in deltas for point in delta.points})

    def series_ids(deltas: tuple[Delta, ...] | list[Delta]) -> list[str]:
        return sorted({str(point["series_id"]) for delta in deltas for point in delta.points})

    for bucket_start in range(start_unix_nano, end_unix_nano, BUCKET_NANOSECONDS_60S):
        bucket_end = bucket_start + BUCKET_NANOSECONDS_60S
        subwindow_starts = range(bucket_start, bucket_end, CADENCE * NANO)
        subwindow_bounds = [(sub_start, sub_start + CADENCE * NANO) for sub_start in subwindow_starts]
        cpu_deltas = [_delta(by_role["cpu"], sub_start, sub_end) for sub_start, sub_end in subwindow_bounds]
        request_deltas = [_delta(by_role["requests"], sub_start, sub_end) for sub_start, sub_end in subwindow_bounds]
        duration_deltas = [_delta(by_role["duration"], sub_start, sub_end) for sub_start, sub_end in subwindow_bounds]

        def states(deltas: list[Delta]) -> list[dict[str, Any]]:
            return [
                {
                    "window_start_unix_nano": str(sub_start),
                    "window_end_unix_nano": str(sub_end),
                    "coverage_state": delta.state,
                    "reason": delta.reason,
                }
                for (sub_start, sub_end), delta in zip(subwindow_bounds, deltas)
            ]

        cpu_state, cpu_reason = _unavailable(*cpu_deltas)
        request_state, request_reason = _unavailable(*request_deltas)
        latency_state, latency_reason = _unavailable(*(request_deltas + duration_deltas))
        cpu_value = sum(delta.value for delta in cpu_deltas) / BUCKET_SECONDS_60S if cpu_state == "complete" else None
        total_requests = sum(delta.value for delta in request_deltas) if request_state == "complete" else None
        request_rate = total_requests / BUCKET_SECONDS_60S if total_requests is not None else None
        total_duration = sum(delta.value for delta in duration_deltas) if all(delta.state == "complete" for delta in duration_deltas) else None
        latency_value = None

        if latency_state == "complete":
            identities_match = all(
                {_api_pair_identity(point) for point in request_delta.points}
                == {_api_pair_identity(point) for point in duration_delta.points}
                for request_delta, duration_delta in zip(request_deltas, duration_deltas)
            )
            if not identities_match:
                latency_state, latency_reason = "invalid", "api_identity_mismatch"
            elif total_requests == 0:
                if total_duration == 0:
                    latency_state, latency_reason = "not_applicable", "no_observed_increment"
                else:
                    latency_state, latency_reason = "invalid", "duration_without_responses"
            else:
                latency_value = total_duration / total_requests

        if (
            request_state == "complete"
            and total_requests == 0
            and all(delta.state == "complete" for delta in duration_deltas)
        ):
            request_reason = "no_observed_increment"
        cpu_provenance = {
            "source_series_ids": series_ids(cpu_deltas),
            "source_raw_point_ids": point_ids(cpu_deltas),
            "formula": formula_by_metric["cpu_cores"],
            "input_cadence_seconds": CADENCE,
            "subwindow_coverage": states(cpu_deltas),
        }
        request_provenance = {
            "source_series_ids": series_ids(request_deltas),
            "source_raw_point_ids": point_ids(request_deltas),
            "formula": formula_by_metric["success_response_rate"],
            "input_cadence_seconds": CADENCE,
            "subwindow_coverage": states(request_deltas),
        }
        latency_provenance = {
            "source_series_ids": series_ids(request_deltas + duration_deltas),
            "source_raw_point_ids": point_ids(request_deltas + duration_deltas),
            "formula": formula_by_metric["success_latency_mean_ms"],
            "input_cadence_seconds": CADENCE,
            "request_subwindow_coverage": states(request_deltas),
            "duration_subwindow_coverage": states(duration_deltas),
        }
        outputs = (
            ("cpu_cores", cpu_value, cpu_state, cpu_reason, cpu_deltas, cpu_provenance),
            ("success_response_rate", request_rate, request_state, request_reason, request_deltas, request_provenance),
            ("success_latency_mean_ms", latency_value, latency_state, latency_reason, request_deltas + duration_deltas, latency_provenance),
        )
        for metric, value, state, reason, deltas, provenance in outputs:
            unit, _ = METRICS[metric]
            rows.append({
                "metric_name": metric,
                "service_name": service_name,
                "instance_id": instance_id,
                "window_start_unix_nano": bucket_start,
                "window_end_unix_nano": bucket_end,
                "value": value,
                "unit": unit,
                "coverage_state": state,
                "reason": reason,
                "source_raw_point_ids": point_ids(deltas),
                "provenance": provenance,
            })

    summary = {
        "input_raw_points": len(raw_points),
        "visible_start_unix_nano": str(start_unix_nano),
        "visible_end_unix_nano": str(end_unix_nano),
        "window_seconds": BUCKET_SECONDS_60S,
        "input_cadence_seconds": CADENCE,
        "visible_windows": (end_unix_nano - start_unix_nano) // BUCKET_NANOSECONDS_60S,
        "coverage_rows": len(rows),
        "numeric_derived_points": sum(row["value"] is not None for row in rows),
        "metrics": {
            metric: {
                "coverage": dict(Counter(row["coverage_state"] for row in rows if row["metric_name"] == metric)),
                "reasons": dict(Counter(row["reason"] for row in rows if row["metric_name"] == metric and row["reason"])),
                "positive_value_count": sum(
                    row["value"] is not None and row["value"] > 0
                    for row in rows
                    if row["metric_name"] == metric
                ),
            }
            for metric in METRICS
        },
    }
    return rows, summary


def run_transform_60s(
    repository: Any,
    replay_run_id: str,
    until_unix_nano: int | None = None,
) -> dict[str, Any]:
    """Persist an immutable 60-second aggregate through the latest complete bucket."""
    replay = repository.get_replay(replay_run_id)
    if replay is None:
        raise ValueError("Replay not found")
    persisted_points = repository.get_raw_points(replay_run_id)
    if not persisted_points:
        raise ValueError("Replay has no committed raw points; OTLP ingestion is required before batch")
    start = int(replay["display_start_unix_nano"])
    display_end = int(replay["display_end_unix_nano"])
    persisted_watermark = max(int(point["time_unix_nano"]) for point in persisted_points)
    source_watermark = persisted_watermark if until_unix_nano is None else int(until_unix_nano)
    if source_watermark > display_end:
        raise ValueError("Transform watermark cannot exceed the replay display end")
    if source_watermark > persisted_watermark:
        raise ValueError("Transform watermark exceeds the latest persisted source timestamp")
    if source_watermark <= start or (source_watermark - start) % (CADENCE * NANO):
        raise ValueError("60-second transform watermark must be on the 15-second source grid")
    end = start + ((source_watermark - start) // BUCKET_NANOSECONDS_60S) * BUCKET_NANOSECONDS_60S
    if end <= start:
        raise ValueError("No complete 60-second bucket is available through this watermark")
    raw_points = [point for point in persisted_points if int(point["time_unix_nano"]) <= end]
    if not raw_points:
        raise ValueError("No committed source points are available through the last complete 60-second bucket")
    config = {
        "window_seconds": BUCKET_SECONDS_60S,
        "input_cadence_seconds": CADENCE,
        "bucket_alignment": "display_start",
        "bucket_origin_unix_nano": str(start),
        "display_start_unix_nano": str(start),
        "display_end_unix_nano": str(end),
        "latest_persisted_source_timestamp_unix_nano": str(persisted_watermark),
        "complete_bucket_policy": "discard_trailing_partial",
        "service_name": replay["service_name"],
        "instance_id": replay["instance_id"],
        "warmup_delta_displayed": False,
        "missing_policy": "no_imputation; require_four_complete_15_second_deltas",
        "counter_decrease_policy": "invalid_no_delta",
        "input": "committed_postgresql_raw_points",
        "formulas": {
            "cpu_cores": "sum(four delta(cpu_seconds))/60",
            "success_response_rate": "sum(four delta(grpc.200.0_responses))/60",
            "success_latency_mean_ms": "sum(four delta(grpc.200.0_duration_ms))/sum(four delta(grpc.200.0_responses))",
        },
        "input_raw_point_ids": sorted(point["id"] for point in raw_points),
        "input_raw_point_count": len(raw_points),
        "input_snapshot_sha256": hashlib.sha256(
            json.dumps(raw_points, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest(),
    }
    transform_run_id = repository.start_transform_run(replay_run_id, TRANSFORM_60S_VERSION, config)
    try:
        rows, summary = derive_observations_60s(
            raw_points,
            start_unix_nano=start,
            end_unix_nano=end,
            service_name=replay["service_name"],
            instance_id=replay["instance_id"],
        )
        repository.write_transform_results(transform_run_id, rows)
        repository.finish_transform_run(transform_run_id, status="complete", summary=summary)
    except Exception:
        repository.finish_transform_run(transform_run_id, status="failed", error="transform_execution_failed")
        raise
    return {
        "replay_run_id": replay_run_id,
        "transform_run_id": str(transform_run_id),
        "version": TRANSFORM_60S_VERSION,
        "status": "complete",
        "summary": summary,
    }
