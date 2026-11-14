"""Send original source samples using OTLP/HTTP binary Protobuf."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
    ExportMetricsServiceRequest,
    ExportMetricsServiceResponse,
)
from opentelemetry.proto.metrics.v1.metrics_pb2 import AGGREGATION_TEMPORALITY_CUMULATIVE

from .dataset import DatasetCut, INSTANCE, NANO, REPLAYER_VERSION, SERVICE


def _attribute(container: Any, key: str, value: str | int) -> None:
    entry = container.add(key=key)
    if isinstance(value, int):
        entry.value.int_value = value
    else:
        entry.value.string_value = value


def _point_slice(cut: DatasetCut, start_index: int, end_index: int | None) -> tuple[int, int]:
    if not cut.series:
        raise ValueError("The source cut has no metric series")
    lengths = {len(series.points) for series in cut.series}
    timestamps = {tuple(point.timestamp for point in series.points) for series in cut.series}
    if len(lengths) != 1 or len(timestamps) != 1:
        raise ValueError("Streaming requires the selected series to share the same timestamp sequence")
    point_count = next(iter(lengths))
    stop = point_count if end_index is None else end_index
    if start_index < 0 or stop <= start_index or stop > point_count:
        raise ValueError("The requested source point range is invalid")
    return start_index, stop


def build_request(
    cut: DatasetCut,
    replay_run_id: str,
    start_index: int = 0,
    end_index: int | None = None,
) -> ExportMetricsServiceRequest:
    request = ExportMetricsServiceRequest()
    start, stop = _point_slice(cut, start_index, end_index)
    for series in cut.series:
        resource_metrics = request.resource_metrics.add()
        resource = {
            "service.name": SERVICE, "service.instance.id": INSTANCE,
            "aim.dataset.name": "aiopsarena", "aim.dataset.case": "Case-1",
            "aim.replay.run_id": replay_run_id,
            "aim.source.cmdb_id": series.spec.cmdb_id,
            "aim.source.file_sha256": series.file_sha256,
        }
        for key, value in resource.items():
            _attribute(resource_metrics.resource.attributes, key, value)
        scope = resource_metrics.scope_metrics.add()
        scope.scope.name = "aim.replayer.aiopsarena"
        scope.scope.version = REPLAYER_VERSION
        metric = scope.metrics.add(name=series.spec.metric_name, unit=series.spec.unit)
        metric.sum.aggregation_temporality = AGGREGATION_TEMPORALITY_CUMULATIVE
        metric.sum.is_monotonic = True
        for source_point in series.points[start:stop]:
            point = metric.sum.data_points.add(time_unix_nano=source_point.timestamp * NANO, as_double=source_point.value)
            # StartTimeUnixNano is unknown upstream: preserve its absence (wire default 0).
            _attribute(point.attributes, "aim.source.row_ordinal", source_point.row_ordinal)
            _attribute(point.attributes, "aim.source.cmdb_id", series.spec.cmdb_id)
            _attribute(point.attributes, "aim.source.kpi_name", series.spec.metric_name)
    return request


def send_replay(
    cut: DatasetCut,
    api_url: str,
    replay_run_id: str | None = None,
    start_index: int = 0,
    end_index: int | None = None,
    *,
    metrics_endpoint: str | None = None,
) -> dict[str, Any]:
    """Send one ordered slice; success is the receiver's post-commit OTLP response."""
    base = api_url.rstrip("/")
    start, stop = _point_slice(cut, start_index, end_index)
    with httpx.Client(timeout=60, trust_env=False) as client:
        if replay_run_id is None:
            response = client.post(f"{base}/api/v1/replays", json=cut.replay_payload())
            response.raise_for_status()
            replay_run_id = response.json()["replay_run_id"]
        payload = build_request(cut, replay_run_id, start, stop).SerializeToString(deterministic=True)
        response = client.post(metrics_endpoint or f"{base}/v1/metrics", content=payload, headers={"Content-Type": "application/x-protobuf"})
        response.raise_for_status()
        if response.headers.get("content-type", "").split(";")[0] != "application/x-protobuf":
            raise ValueError("Receiver did not return the OTLP Protobuf content type")
        result = ExportMetricsServiceResponse.FromString(response.content)
        if result.HasField("partial_success") and (result.partial_success.rejected_data_points or result.partial_success.error_message):
            raise ValueError(f"OTLP receiver reported partial success: {result.partial_success.error_message}")
    return {
        "replay_run_id": replay_run_id, "http_status": response.status_code,
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "payload_bytes": len(payload), "series_count": len(cut.series),
        "source_point_count": sum(len(series.points[start:stop]) for series in cut.series),
        "source_point_start_index": start,
        "source_point_end_index": stop,
        "source_time_start_unix_nano": cut.series[0].points[start].timestamp * NANO,
        "source_time_end_unix_nano": cut.series[0].points[stop - 1].timestamp * NANO,
        "source_manifest_sha256": cut.source_manifest["manifest_sha256"],
        "transport": "OTLP/HTTP Protobuf", "derived_before_ingestion": False,
    }


def verify_persisted(cut: DatasetCut, raw_points: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare every source point by identity, timestamp, ordinal, hash and value."""
    expected = {}
    for series in cut.series:
        for point in series.points:
            key = (series.spec.metric_name, series.spec.cmdb_id, point.timestamp * NANO, series.file_sha256, point.row_ordinal)
            expected[key] = point.value
    actual = {}
    for point in raw_points:
        key = (point["metric_name"], point["source_cmdb_id"], int(point["time_unix_nano"]), point["source_file_sha256"], int(point["source_row_ordinal"]))
        if key in actual:
            raise ValueError("Database returned a duplicate source identity")
        actual[key] = float(point["value"])
    missing, extra = expected.keys() - actual.keys(), actual.keys() - expected.keys()
    differing = [key for key in expected.keys() & actual.keys() if expected[key] != actual[key]]
    if missing or extra or differing:
        raise ValueError(f"Raw/source mismatch: {len(missing)} missing, {len(extra)} extra, {len(differing)} different values")
    return {"verified_points": len(actual), "source_series": len(cut.series), "missing_points": 0, "extra_points": 0, "differing_values": 0}
