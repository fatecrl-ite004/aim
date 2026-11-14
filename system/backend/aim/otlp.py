"""The bounded OTLP Metrics/HTTP Protobuf profile used by the V1 replay."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from google.rpc.status_pb2 import Status
from opentelemetry.proto.collector.metrics.v1.metrics_service_pb2 import (
    ExportMetricsServiceRequest,
    ExportMetricsServiceResponse,
)
from opentelemetry.proto.metrics.v1.metrics_pb2 import AGGREGATION_TEMPORALITY_CUMULATIVE

from .dataset import SERIES


OTLP_PROTOBUF_MEDIA_TYPE = "application/x-protobuf"
_SUPPORTED_SERIES = {
    spec.metric_name: {"unit": spec.unit, "cmdb_id": spec.cmdb_id}
    for spec in SERIES
}


@dataclass
class OtlpProfileError(ValueError):
    message: str
    http_status: int = 400
    grpc_code: int = 3  # INVALID_ARGUMENT

    def __str__(self) -> str:
        return self.message


def _any_value(value: Any) -> Any:
    kind = value.WhichOneof("value")
    if kind is None:
        return None
    if kind == "string_value":
        return value.string_value
    if kind == "bool_value":
        return bool(value.bool_value)
    if kind == "int_value":
        return int(value.int_value)
    if kind == "double_value":
        return float(value.double_value)
    if kind == "bytes_value":
        return bytes(value.bytes_value).hex()
    if kind == "array_value":
        return [_any_value(item) for item in value.array_value.values]
    if kind == "kvlist_value":
        return _attributes(value.kvlist_value.values)
    raise OtlpProfileError(f"Unsupported OTLP AnyValue case: {kind}")


def _attributes(attributes: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in attributes:
        if not item.key:
            raise OtlpProfileError("OTLP attribute key cannot be empty")
        if item.key in result:
            raise OtlpProfileError(f"Duplicate OTLP attribute key: {item.key}")
        result[item.key] = _any_value(item.value)
    return result


def _as_required_string(attrs: dict[str, Any], key: str) -> str:
    value = attrs.get(key)
    if not isinstance(value, str) or not value:
        raise OtlpProfileError(f"Required OTLP string attribute {key!r} is missing")
    return value


def decode_metrics_request(payload: bytes) -> tuple[str, list[dict[str, Any]]]:
    """Decode only cumulative monotonic Sum points and retain full attributes."""
    request = ExportMetricsServiceRequest()
    try:
        request.ParseFromString(payload)
    except Exception as exc:
        raise OtlpProfileError("Request body is not a valid ExportMetricsServiceRequest Protobuf") from exc
    if not request.resource_metrics:
        raise OtlpProfileError("At least one ResourceMetrics group is required")

    replay_ids: set[str] = set()
    decoded: list[dict[str, Any]] = []
    for resource_metrics in request.resource_metrics:
        if resource_metrics.schema_url:
            raise OtlpProfileError("schema_url is outside the V1 OTLP profile")
        resource = resource_metrics.resource
        if resource.dropped_attributes_count:
            raise OtlpProfileError("Resource dropped_attributes_count must be zero")
        resource_attrs = _attributes(resource.attributes)
        replay_id = _as_required_string(resource_attrs, "aim.replay.run_id")
        dataset_name = _as_required_string(resource_attrs, "aim.dataset.name")
        dataset_case = _as_required_string(resource_attrs, "aim.dataset.case")
        service_name = _as_required_string(resource_attrs, "service.name")
        instance_id = _as_required_string(resource_attrs, "service.instance.id")
        source_cmdb_id = _as_required_string(resource_attrs, "aim.source.cmdb_id")
        source_file_sha256 = _as_required_string(resource_attrs, "aim.source.file_sha256")
        replay_ids.add(replay_id)

        if not resource_metrics.scope_metrics:
            raise OtlpProfileError("At least one ScopeMetrics group is required")
        for scope_metrics in resource_metrics.scope_metrics:
            if scope_metrics.schema_url:
                raise OtlpProfileError("ScopeMetrics schema_url is outside the V1 OTLP profile")
            scope = scope_metrics.scope
            if scope.dropped_attributes_count:
                raise OtlpProfileError("InstrumentationScope dropped_attributes_count must be zero")
            scope_attrs = _attributes(scope.attributes)
            for metric in scope_metrics.metrics:
                source_spec = _SUPPORTED_SERIES.get(metric.name)
                if source_spec is None:
                    raise OtlpProfileError(f"Metric is outside the AIOpsArena V1 profile: {metric.name!r}")
                if metric.unit != source_spec["unit"]:
                    raise OtlpProfileError(f"Metric {metric.name!r} must use unit {source_spec['unit']!r}")
                if source_cmdb_id != source_spec["cmdb_id"]:
                    raise OtlpProfileError(f"Metric {metric.name!r} has an unsupported source cmdb_id")
                if metric.WhichOneof("data") != "sum":
                    raise OtlpProfileError(f"Only OTLP Sum metrics are supported; got {metric.name!r}")
                if metric.sum.aggregation_temporality != AGGREGATION_TEMPORALITY_CUMULATIVE:
                    raise OtlpProfileError(f"Metric {metric.name!r} must use cumulative temporality")
                if not metric.sum.is_monotonic:
                    raise OtlpProfileError(f"Metric {metric.name!r} must be monotonic")
                if not metric.name:
                    raise OtlpProfileError("OTLP metric name cannot be empty")
                for point in metric.sum.data_points:
                    if point.flags:
                        raise OtlpProfileError("OTLP datapoint flags are outside the V1 profile")
                    if point.exemplars:
                        raise OtlpProfileError("OTLP datapoint exemplars are outside the V1 profile")
                    if not point.time_unix_nano:
                        raise OtlpProfileError(f"Metric {metric.name!r} has a zero TimeUnixNano")
                    datapoint_attrs = _attributes(point.attributes)
                    ordinal = datapoint_attrs.get("aim.source.row_ordinal")
                    if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal <= 0:
                        raise OtlpProfileError("aim.source.row_ordinal must be a positive integer")
                    if datapoint_attrs.get("aim.source.cmdb_id") != source_cmdb_id:
                        raise OtlpProfileError("Resource and datapoint aim.source.cmdb_id do not match")
                    if datapoint_attrs.get("aim.source.kpi_name") != metric.name:
                        raise OtlpProfileError("aim.source.kpi_name must match the OTLP metric name")
                    value_case = point.WhichOneof("value")
                    if value_case == "as_int":
                        value_type, value = "int", int(point.as_int)
                    elif value_case == "as_double":
                        value_type, value = "double", float(point.as_double)
                    else:
                        raise OtlpProfileError("OTLP Sum datapoint must contain as_int or as_double")
                    decoded.append({
                        "replay_run_id": replay_id,
                        "dataset_name": dataset_name,
                        "dataset_case": dataset_case,
                        "service_name": service_name,
                        "instance_id": instance_id,
                        "source_cmdb_id": source_cmdb_id,
                        "source_file_sha256": source_file_sha256,
                        "source_row_ordinal": ordinal,
                        "metric_name": metric.name,
                        "metric_type": "sum",
                        "unit": metric.unit,
                        "aggregation_temporality": int(metric.sum.aggregation_temporality),
                        "is_monotonic": True,
                        "scope_name": scope.name,
                        "scope_version": scope.version,
                        "scope_attributes": scope_attrs,
                        "resource_attributes": resource_attrs,
                        "datapoint_attributes": datapoint_attrs,
                        "source_timestamp_unix_nano": int(point.time_unix_nano),
                        "start_time_unix_nano": int(point.start_time_unix_nano) if point.start_time_unix_nano else None,
                        "value_type": value_type,
                        "value": value,
                    })

    if len(replay_ids) != 1:
        raise OtlpProfileError("An OTLP request must contain exactly one aim.replay.run_id")
    if not decoded:
        raise OtlpProfileError("At least one numeric datapoint is required")
    return next(iter(replay_ids)), decoded


def success_payload() -> bytes:
    return ExportMetricsServiceResponse().SerializeToString()


def status_payload(code: int, message: str) -> bytes:
    status = Status(code=code, message=message)
    return status.SerializeToString()
