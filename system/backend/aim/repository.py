"""PostgreSQL repository for replay ingestion, transformation, and read APIs."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime
from typing import Any, Iterable

import psycopg
from psycopg.types.json import Jsonb

from .db import connection


class RepositoryError(RuntimeError):
    """Base class for domain errors mapped by the HTTP layer."""


class NotFound(RepositoryError):
    pass


class Conflict(RepositoryError):
    pass


class InvalidData(RepositoryError):
    pass


_TECHNICAL_RESOURCE_ATTRIBUTES = {"aim.source.file_sha256", "aim.replay.run_id"}
_TECHNICAL_POINT_ATTRIBUTES = {"aim.source.row_ordinal"}
_ROLE_METRICS = {
    "cpu": "container_cpu_usage_seconds_total",
    "requests": "istio_requests_total.grpc.200.0",
    "duration": "istio_request_duration_milliseconds_sum.grpc.200.0",
}


def _uuid(value: str | uuid.UUID | None = None) -> uuid.UUID:
    if value is None:
        return uuid.uuid4()
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise InvalidData(f"Invalid UUID: {value}") from exc


def _ns(value: Any, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise InvalidData(f"{name} must be an integer Unix-nanosecond value") from exc
    if result < 0 or result >= 2**64:
        raise InvalidData(f"{name} is outside the unsigned 64-bit Unix-nanosecond range")
    return result


def _sha256(value: Any, name: str) -> str:
    candidate = str(value or "").lower()
    if len(candidate) != 64 or any(char not in "0123456789abcdef" for char in candidate):
        raise InvalidData(f"{name} must be a 64-character lowercase SHA-256 hex digest")
    return candidate


def _json_digest(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return dict(value or {})


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _plain_replay(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    result["replay_run_id"] = str(result["replay_run_id"])
    for key in ("raw_start_unix_nano", "raw_end_unix_nano", "display_start_unix_nano", "display_end_unix_nano"):
        result[key] = int(result[key])
    result["source_name"] = result.pop("dataset")
    result["case_id"] = result.pop("dataset_case")
    result["created_at"] = _iso(result.get("created_at"))
    result["completed_at"] = _iso(result.get("completed_at"))
    return result


def _attr_map(attributes: Any) -> dict[str, Any]:
    return _json_dict(attributes)


def _semantic_attributes(attributes: dict[str, Any], excluded: set[str]) -> dict[str, Any]:
    return {key: value for key, value in attributes.items() if key not in excluded}


def _typed_number(value_type: str, value_int: int | None, value_double: float | None) -> int | float:
    """Keep OTLP int64 values exact; never route them through a SQL float CASE."""
    if value_type == "int" and value_int is not None and value_double is None:
        return int(value_int)
    if value_type == "double" and value_double is not None and value_int is None:
        return float(value_double)
    raise InvalidData("Persisted raw point has an inconsistent numeric representation")


class Repository:
    """Thin SQL repository. Each public write method owns one transaction."""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn

    def check_ready(self) -> bool:
        with connection(self.dsn) as conn:
            row = conn.execute("SELECT to_regclass('public.replay_run') AS replay_table").fetchone()
            return bool(row and row["replay_table"])

    def create_replay(self, payload: dict[str, Any]) -> dict[str, Any]:
        dataset = str(payload.get("dataset") or payload.get("source_name") or "").strip()
        dataset_case = str(payload.get("dataset_case") or payload.get("case_id") or "").strip()
        service_name = str(payload.get("service_name") or "").strip()
        instance_id = str(payload.get("instance_id") or "").strip()
        if not all((dataset, dataset_case, service_name, instance_id)):
            raise InvalidData("dataset, dataset_case, service_name, and instance_id are required")

        source_manifest = payload.get("source_manifest")
        if not isinstance(source_manifest, dict) or not isinstance(source_manifest.get("files"), list):
            raise InvalidData("source_manifest.files must be a list")
        files = source_manifest["files"]
        roles: dict[str, str] = {}
        for item in files:
            if not isinstance(item, dict):
                raise InvalidData("each source_manifest.files entry must be an object")
            role = str(item.get("role") or "")
            digest = _sha256(item.get("sha256"), f"source_manifest.files[{role}].sha256")
            if role in roles:
                raise InvalidData(f"duplicate source file role: {role}")
            roles[role] = digest
            if not str(item.get("relative_path") or ""):
                raise InvalidData(f"source_manifest.files[{role}].relative_path is required")
        if dataset.lower() == "aiopsarena" and set(roles) != {"cpu", "requests", "duration", "ground_truth"}:
            raise InvalidData("AIOpsArena manifest must contain cpu, requests, duration, and ground_truth files")
        manifest_sha = _sha256(source_manifest.get("manifest_sha256"), "source_manifest.manifest_sha256")
        if _json_digest(files) != manifest_sha:
            raise InvalidData("source_manifest.manifest_sha256 does not match its files list")

        raw_start = _ns(payload.get("raw_start_unix_nano"), "raw_start_unix_nano")
        raw_end = _ns(payload.get("raw_end_unix_nano"), "raw_end_unix_nano")
        display_start = _ns(payload.get("display_start_unix_nano"), "display_start_unix_nano")
        display_end = _ns(payload.get("display_end_unix_nano"), "display_end_unix_nano")
        if not raw_start <= display_start < display_end <= raw_end:
            raise InvalidData("display window must be inside the raw source window")

        replay_id, service_id, instance_pk = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        replayer_version = str(payload.get("replayer_version") or "unknown")
        mapping_version = str(payload.get("mapping_version") or "unknown")
        with connection(self.dsn) as conn:
            row = conn.execute(
                """INSERT INTO replay_run (
                       replay_run_id,dataset,dataset_case,service_name,instance_id,source_manifest,
                       replayer_version,mapping_version,raw_start_unix_nano,raw_end_unix_nano,
                       display_start_unix_nano,display_end_unix_nano,status
                   ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'created')
                   RETURNING *""",
                (replay_id, dataset, dataset_case, service_name, instance_id, Jsonb(source_manifest),
                 replayer_version, mapping_version, raw_start, raw_end, display_start, display_end),
            ).fetchone()
            conn.execute(
                "INSERT INTO service_entity(service_id,replay_run_id,service_name) VALUES (%s,%s,%s)",
                (service_id, replay_id, service_name),
            )
            conn.execute(
                """INSERT INTO service_instance(service_instance_id,replay_run_id,service_id,instance_name)
                   VALUES (%s,%s,%s,%s)""",
                (instance_pk, replay_id, service_id, instance_id),
            )
        return _plain_replay(row)

    def get_replay(self, replay_id: str | uuid.UUID) -> dict[str, Any] | None:
        replay_uuid = _uuid(replay_id)
        with connection(self.dsn) as conn:
            row = conn.execute("SELECT * FROM replay_run WHERE replay_run_id=%s", (replay_uuid,)).fetchone()
        return _plain_replay(row) if row else None

    def list_replays(self) -> list[dict[str, Any]]:
        with connection(self.dsn) as conn:
            rows = conn.execute(
                "SELECT * FROM replay_run ORDER BY created_at DESC, replay_run_id DESC"
            ).fetchall()
        return [_plain_replay(row) for row in rows]

    def _replay_row(
        self,
        conn: psycopg.Connection,
        replay_id: str | uuid.UUID,
        *,
        for_update: bool = False,
    ) -> dict[str, Any]:
        suffix = " FOR UPDATE" if for_update else ""
        row = conn.execute(
            f"SELECT * FROM replay_run WHERE replay_run_id=%s{suffix}", (_uuid(replay_id),)
        ).fetchone()
        if row is None:
            raise NotFound("Replay not found")
        return row

    def record_batch_and_raw_points(
        self,
        replay_id: str | uuid.UUID,
        payload_sha256: str,
        points: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Atomically persist an accepted OTLP request and all its raw points."""
        replay_uuid = _uuid(replay_id)
        payload_sha = _sha256(payload_sha256, "payload_sha256")
        if not points:
            raise InvalidData("empty metrics requests are not accepted by this AIM profile")
        inserted = 0
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid, for_update=True)
            manifest = _json_dict(replay["source_manifest"])
            role_hashes = {item["role"]: item["sha256"] for item in manifest["files"]}
            transform_started = bool(conn.execute(
                "SELECT 1 FROM transform_run WHERE replay_run_id=%s LIMIT 1", (replay_uuid,)
            ).fetchone()) or replay["status"] in {"processing", "processed"}
            transform_running = bool(conn.execute(
                "SELECT 1 FROM transform_run WHERE replay_run_id=%s AND status='running' LIMIT 1", (replay_uuid,)
            ).fetchone())
            previous_watermark = None
            if transform_started:
                previous = conn.execute(
                    "SELECT MAX(source_timestamp_unix_nano) AS watermark FROM raw_metric_point WHERE replay_run_id=%s",
                    (replay_uuid,),
                ).fetchone()
                previous_watermark = int(previous["watermark"]) if previous["watermark"] is not None else None
            batch_id = uuid.uuid4()
            batch = conn.execute(
                """INSERT INTO ingest_batch(ingest_batch_id,replay_run_id,payload_sha256,status,accepted_data_points)
                   VALUES (%s,%s,%s,'accepted',%s)
                   ON CONFLICT (replay_run_id,payload_sha256) DO NOTHING
                   RETURNING ingest_batch_id""",
                (batch_id, replay_uuid, payload_sha, len(points)),
            ).fetchone()
            if batch:
                batch_id = batch["ingest_batch_id"]
            else:
                batch = conn.execute(
                    "SELECT ingest_batch_id FROM ingest_batch WHERE replay_run_id=%s AND payload_sha256=%s",
                    (replay_uuid, payload_sha),
                ).fetchone()
                batch_id = batch["ingest_batch_id"]

            for point in points:
                self._validate_point_against_replay(point, replay_uuid, replay, role_hashes)
                raw_id, did_insert = self._insert_raw_point(conn, replay_uuid, batch_id, point)
                inserted += int(did_insert)
                if transform_running and did_insert:
                    raise Conflict("New raw points cannot be appended while a transform run is active")
                if transform_started and did_insert and (
                    previous_watermark is None
                    or int(point["source_timestamp_unix_nano"]) <= previous_watermark
                ):
                    raise Conflict(
                        "New raw points after transform runs must append strictly after the persisted timestamp watermark"
                    )
            if inserted:
                conn.execute(
                    "UPDATE replay_run SET status='ingested' WHERE replay_run_id=%s AND status IN ('created','ingesting','processed')",
                    (replay_uuid,),
                )
        return {"ingest_batch_id": str(batch_id), "accepted_data_points": len(points), "inserted_data_points": inserted}

    def _validate_point_against_replay(
        self,
        point: dict[str, Any],
        replay_uuid: uuid.UUID,
        replay: dict[str, Any],
        role_hashes: dict[str, str],
    ) -> None:
        if str(point.get("replay_run_id")) != str(replay_uuid):
            raise InvalidData("OTLP point replay id does not match the selected replay")
        resources = _attr_map(point.get("resource_attributes"))
        attrs = _attr_map(point.get("datapoint_attributes"))
        if resources.get("aim.replay.run_id") != str(replay_uuid):
            raise InvalidData("Resource aim.replay.run_id is missing or does not match")
        if resources.get("aim.dataset.name") != replay["dataset"] or resources.get("aim.dataset.case") != replay["dataset_case"]:
            raise InvalidData("OTLP dataset identity does not match the registered replay")
        if resources.get("service.name") != replay["service_name"] or resources.get("service.instance.id") != replay["instance_id"]:
            raise InvalidData("OTLP service identity does not match the registered replay")
        cmdb_id = str(resources.get("aim.source.cmdb_id") or "")
        if not cmdb_id or attrs.get("aim.source.cmdb_id") != cmdb_id:
            raise InvalidData("Resource and datapoint source cmdb_id must match")
        metric_name = str(point.get("metric_name") or "")
        if attrs.get("aim.source.kpi_name") != metric_name:
            raise InvalidData("datapoint aim.source.kpi_name must match the OTLP metric name")
        source_hash = _sha256(resources.get("aim.source.file_sha256"), "aim.source.file_sha256")
        ordinal = attrs.get("aim.source.row_ordinal")
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal <= 0:
            raise InvalidData("aim.source.row_ordinal must be a positive integer")
        if source_hash not in role_hashes.values():
            raise InvalidData("OTLP source file hash is not present in the replay manifest")
        if str(point.get("metric_name")) not in _ROLE_METRICS.values():
            raise InvalidData(f"Metric is outside the AIOpsArena V1 replay profile: {metric_name}")
        matching_roles = {role for role, name in _ROLE_METRICS.items() if name == metric_name}
        if not any(role_hashes.get(role) == source_hash for role in matching_roles):
            raise InvalidData("OTLP metric name and source file hash do not match the replay manifest")
        if point.get("service_name") != replay["service_name"] or point.get("instance_id") != replay["instance_id"]:
            raise InvalidData("Normalized point service identity does not match the replay")
        timestamp = _ns(point.get("source_timestamp_unix_nano"), "TimeUnixNano")
        if not int(replay["raw_start_unix_nano"]) <= timestamp <= int(replay["raw_end_unix_nano"]):
            raise InvalidData("OTLP point timestamp is outside the replay raw window")
        if _ns(point.get("source_row_ordinal"), "source_row_ordinal") != ordinal:
            raise InvalidData("Normalized point ordinal differs from its OTLP attribute")
        if point.get("source_file_sha256") != source_hash:
            raise InvalidData("Normalized point file hash differs from its OTLP resource attribute")

    def _insert_raw_point(
        self,
        conn: psycopg.Connection,
        replay_uuid: uuid.UUID,
        batch_id: uuid.UUID,
        point: dict[str, Any],
    ) -> tuple[int, bool]:
        service_row = conn.execute(
            "SELECT service_id FROM service_entity WHERE replay_run_id=%s AND service_name=%s",
            (replay_uuid, point["service_name"]),
        ).fetchone()
        if not service_row:
            raise InvalidData("Service is not registered for this replay")
        instance_row = conn.execute(
            """SELECT service_instance_id FROM service_instance
               WHERE replay_run_id=%s AND service_id=%s AND instance_name=%s""",
            (replay_uuid, service_row["service_id"], point["instance_id"]),
        ).fetchone()
        if not instance_row:
            raise InvalidData("Service instance is not registered for this replay")

        metric_name = str(point["metric_name"])
        metric_type = str(point.get("metric_type") or "sum")
        unit = str(point.get("unit") or "")
        temporality = int(point.get("aggregation_temporality") or 0)
        monotonic = bool(point.get("is_monotonic"))
        metric_def = conn.execute(
            """INSERT INTO source_metric_definition(
                   source_metric_definition_id,metric_name,metric_type,unit,aggregation_temporality,is_monotonic
               ) VALUES (%s,%s,%s,%s,%s,%s)
               ON CONFLICT (metric_name,metric_type,unit,aggregation_temporality,is_monotonic)
               DO UPDATE SET metric_name=EXCLUDED.metric_name
               RETURNING source_metric_definition_id""",
            (uuid.uuid4(), metric_name, metric_type, unit, temporality, monotonic),
        ).fetchone()

        resource_attrs = _attr_map(point.get("resource_attributes"))
        point_attrs = _attr_map(point.get("datapoint_attributes"))
        scope_attrs = _attr_map(point.get("scope_attributes"))
        scope_name = str(point.get("scope_name") or "")
        scope_version = str(point.get("scope_version") or "")
        source_cmdb = str(point["source_cmdb_id"])
        normalized = {
            "resource": _semantic_attributes(resource_attrs, _TECHNICAL_RESOURCE_ATTRIBUTES),
            "scope": {"name": scope_name, "version": scope_version, "attributes": scope_attrs},
            "metric": {"name": metric_name, "type": metric_type, "unit": unit,
                       "aggregation_temporality": temporality, "is_monotonic": monotonic},
            "datapoint_attributes": _semantic_attributes(point_attrs, _TECHNICAL_POINT_ATTRIBUTES),
            "source_cmdb_id": source_cmdb,
        }
        canonical = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        fingerprint = hashlib.sha256(canonical).hexdigest()
        series = conn.execute(
            """INSERT INTO metric_series(
                   metric_series_id,service_instance_id,source_metric_definition_id,source_cmdb_id,
                   scope_name,scope_version,scope_attributes,normalized_attributes,series_fingerprint
               ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (service_instance_id,series_fingerprint) DO NOTHING
               RETURNING metric_series_id""",
            (uuid.uuid4(), instance_row["service_instance_id"], metric_def["source_metric_definition_id"],
             source_cmdb, scope_name, scope_version, Jsonb(scope_attrs), Jsonb(normalized), fingerprint),
        ).fetchone()
        if series:
            series_id = series["metric_series_id"]
        else:
            series = conn.execute(
                """SELECT metric_series_id,source_metric_definition_id,source_cmdb_id,normalized_attributes
                   FROM metric_series WHERE service_instance_id=%s AND series_fingerprint=%s""",
                (instance_row["service_instance_id"], fingerprint),
            ).fetchone()
            if (series["source_metric_definition_id"] != metric_def["source_metric_definition_id"]
                    or series["source_cmdb_id"] != source_cmdb or series["normalized_attributes"] != normalized):
                raise Conflict("Series fingerprint collision")
            series_id = series["metric_series_id"]

        value_type = str(point["value_type"])
        value = point["value"]
        value_int = None
        value_double = None
        if value_type == "int":
            if isinstance(value, bool) or not isinstance(value, int) or not -(2**63) <= value < 2**63:
                raise InvalidData("OTLP integer datapoint must fit signed int64")
            value_int = value
        elif value_type == "double":
            value_double = float(value)
            if not math.isfinite(value_double):
                raise InvalidData("OTLP double datapoint must be finite")
        else:
            raise InvalidData("OTLP datapoint value_type must be int or double")

        source_hash = _sha256(point["source_file_sha256"], "source_file_sha256")
        source_ordinal = int(point["source_row_ordinal"])
        timestamp = _ns(point["source_timestamp_unix_nano"], "TimeUnixNano")
        start_time = point.get("start_time_unix_nano")
        if start_time is not None:
            start_time = _ns(start_time, "StartTimeUnixNano")
        candidate = conn.execute(
            """INSERT INTO raw_metric_point(
                   replay_run_id,ingest_batch_id,metric_series_id,source_timestamp_unix_nano,start_time_unix_nano,
                   value_type,value_int,value_double,source_file_sha256,source_row_ordinal,
                   resource_attributes,scope_attributes,datapoint_attributes
               ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (replay_run_id,source_file_sha256,source_row_ordinal) DO NOTHING
               RETURNING raw_metric_point_id""",
            (replay_uuid, batch_id, series_id, timestamp, start_time, value_type, value_int, value_double,
             source_hash, source_ordinal, Jsonb(resource_attrs), Jsonb(scope_attrs), Jsonb(point_attrs)),
        ).fetchone()
        if candidate:
            return int(candidate["raw_metric_point_id"]), True

        existing = conn.execute(
            """SELECT raw_metric_point_id,metric_series_id,source_timestamp_unix_nano,start_time_unix_nano,
                      value_type,value_int,value_double,resource_attributes,scope_attributes,datapoint_attributes
               FROM raw_metric_point
               WHERE replay_run_id=%s AND source_file_sha256=%s AND source_row_ordinal=%s""",
            (replay_uuid, source_hash, source_ordinal),
        ).fetchone()
        expected_value = value_int if value_type == "int" else value_double
        existing_value = existing["value_int"] if existing["value_type"] == "int" else existing["value_double"]
        same = (
            existing["metric_series_id"] == series_id
            and int(existing["source_timestamp_unix_nano"]) == timestamp
            and (int(existing["start_time_unix_nano"]) if existing["start_time_unix_nano"] is not None else None) == start_time
            and existing["value_type"] == value_type
            and existing_value == expected_value
            and existing["resource_attributes"] == resource_attrs
            and existing["scope_attributes"] == scope_attrs
            and existing["datapoint_attributes"] == point_attrs
        )
        if not same:
            raise Conflict("A source row ordinal was replayed with conflicting metric identity or value")
        return int(existing["raw_metric_point_id"]), False

    def get_raw_points(self, replay_id: str | uuid.UUID) -> list[dict[str, Any]]:
        replay_uuid = _uuid(replay_id)
        with connection(self.dsn) as conn:
            rows = conn.execute(
                """SELECT p.raw_metric_point_id AS id,p.metric_series_id AS series_id,
                          d.metric_name,d.unit,e.service_name,i.instance_name AS instance_id,
                          p.source_timestamp_unix_nano AS time_unix_nano,p.start_time_unix_nano,
                          p.value_type,p.value_int,p.value_double,
                          p.source_file_sha256,p.source_row_ordinal,s.source_cmdb_id,
                          s.scope_name,s.scope_version,s.scope_attributes,p.resource_attributes,p.datapoint_attributes,
                          d.metric_type,d.aggregation_temporality,d.is_monotonic
                   FROM raw_metric_point p
                   JOIN metric_series s USING(metric_series_id)
                   JOIN source_metric_definition d USING(source_metric_definition_id)
                   JOIN service_instance i USING(service_instance_id)
                   JOIN service_entity e USING(service_id)
                   WHERE p.replay_run_id=%s
                   ORDER BY d.metric_name,p.source_timestamp_unix_nano,p.source_file_sha256,p.source_row_ordinal""",
                (replay_uuid,),
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["id"] = int(item["id"])
            item["series_id"] = str(item["series_id"])
            item["time_unix_nano"] = int(item["time_unix_nano"])
            item["start_time_unix_nano"] = int(item["start_time_unix_nano"]) if item["start_time_unix_nano"] is not None else None
            item["value"] = _typed_number(item["value_type"], item["value_int"], item["value_double"])
            item["source_row_ordinal"] = int(item["source_row_ordinal"])
            result.append(item)
        return result

    def import_ground_truth(self, replay_id: str | uuid.UUID, events: list[dict[str, Any]]) -> dict[str, Any]:
        replay_uuid = _uuid(replay_id)
        if not events:
            raise InvalidData("at least one ground truth event is required")
        inserted = 0
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid)
            manifest = _json_dict(replay["source_manifest"])
            ground_truth_hashes = {
                item["sha256"] for item in manifest["files"] if item.get("role") == "ground_truth"
            }
            if len(ground_truth_hashes) != 1:
                raise InvalidData("replay manifest must identify one ground_truth file")
            source_hash_expected = next(iter(ground_truth_hashes))
            instance = conn.execute(
                """SELECT service_instance_id FROM service_instance
                   WHERE replay_run_id=%s AND instance_name=%s""",
                (replay_uuid, replay["instance_id"]),
            ).fetchone()
            if not instance:
                raise InvalidData("Replay service instance is not registered")
            for event in events:
                source_hash = _sha256(event.get("source_file_sha256"), "ground truth source_file_sha256")
                if source_hash != source_hash_expected:
                    raise InvalidData("Ground truth event hash does not match the replay manifest")
                ordinal = int(event.get("source_event_ordinal", 0))
                if ordinal <= 0:
                    raise InvalidData("source_event_ordinal must be positive")
                if event.get("event_type") != "injected_fault":
                    raise InvalidData("ground truth event_type must be injected_fault")
                if event.get("service_name") != replay["service_name"] or event.get("instance_id") != replay["instance_id"]:
                    raise InvalidData("Ground truth service identity does not match the replay")
                start = _ns(event.get("start_unix_nano"), "ground truth start_unix_nano")
                end = _ns(event.get("end_unix_nano"), "ground truth end_unix_nano")
                if not start < end:
                    raise InvalidData("Ground truth end must be later than start")
                existing = conn.execute(
                    """SELECT ground_truth_event_id,start_unix_nano,end_unix_nano,failure_type,event_type,
                              service_instance_id FROM ground_truth_event
                       WHERE replay_run_id=%s AND source_file_sha256=%s AND source_event_ordinal=%s""",
                    (replay_uuid, source_hash, ordinal),
                ).fetchone()
                if existing:
                    if (int(existing["start_unix_nano"]) != start or int(existing["end_unix_nano"]) != end
                            or existing["failure_type"] != event.get("failure_type")
                            or existing["event_type"] != event.get("event_type")
                            or existing["service_instance_id"] != instance["service_instance_id"]):
                        raise Conflict("Ground truth event ordinal conflicts with persisted event")
                    continue
                conn.execute(
                    """INSERT INTO ground_truth_event(
                           ground_truth_event_id,replay_run_id,service_instance_id,event_type,failure_type,
                           start_unix_nano,end_unix_nano,source_file_sha256,source_event_ordinal,attributes
                       ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (uuid.uuid4(), replay_uuid, instance["service_instance_id"], event["event_type"],
                     str(event["failure_type"]), start, end, source_hash, ordinal,
                     Jsonb({"service_name": event["service_name"], "instance_id": event["instance_id"]})),
                )
                inserted += 1
        return {"replay_run_id": str(replay_uuid), "event_count": len(events), "inserted_events": inserted}

    def start_transform_run(self, replay_id: str | uuid.UUID, version: str, config: dict[str, Any]) -> str:
        replay_uuid = _uuid(replay_id)
        if not version:
            raise InvalidData("transform version is required")
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid, for_update=True)
            if conn.execute(
                "SELECT 1 FROM transform_run WHERE replay_run_id=%s AND status='running' LIMIT 1", (replay_uuid,)
            ).fetchone():
                raise Conflict("A transform run is already active for this replay")
            raw_count = conn.execute("SELECT count(*) AS n FROM raw_metric_point WHERE replay_run_id=%s", (replay_uuid,)).fetchone()["n"]
            if not raw_count:
                raise InvalidData("Cannot process a replay without persisted raw points")
            transform_id = uuid.uuid4()
            conn.execute(
                """INSERT INTO transform_run(transform_run_id,replay_run_id,version,config,status)
                   VALUES (%s,%s,%s,%s,'running')""",
                (transform_id, replay_uuid, version, Jsonb(config or {})),
            )
            conn.execute("UPDATE replay_run SET status='processing' WHERE replay_run_id=%s", (replay_uuid,))
        return str(transform_id)

    def write_transform_results(self, transform_id: str | uuid.UUID, rows: list[dict[str, Any]]) -> None:
        transform_uuid = _uuid(transform_id)
        with connection(self.dsn) as conn:
            transform = conn.execute(
                "SELECT * FROM transform_run WHERE transform_run_id=%s FOR UPDATE", (transform_uuid,)
            ).fetchone()
            if not transform:
                raise NotFound("Transform run not found")
            if transform["status"] != "running":
                raise Conflict("Transform results can only be written while the run is active")
            replay_uuid = transform["replay_run_id"]
            for item in rows:
                metric_name = str(item["metric_name"])
                unit = str(item["unit"])
                definition = conn.execute(
                    """INSERT INTO derived_metric_definition(derived_metric_definition_id,metric_name,unit,description)
                       VALUES (%s,%s,%s,%s)
                       ON CONFLICT (metric_name,unit) DO UPDATE SET description=EXCLUDED.description
                       RETURNING derived_metric_definition_id""",
                    (uuid.uuid4(), metric_name, unit, str(item.get("description") or "")),
                ).fetchone()
                service_name = str(item["service_name"])
                instance_name = str(item["instance_id"])
                instance = conn.execute(
                    """SELECT i.service_instance_id FROM service_instance i
                       JOIN service_entity e USING(service_id)
                       WHERE i.replay_run_id=%s AND e.service_name=%s AND i.instance_name=%s""",
                    (replay_uuid, service_name, instance_name),
                ).fetchone()
                if not instance:
                    raise InvalidData("Transform row service/instance is not part of the replay")
                window_start = _ns(item["window_start_unix_nano"], "window_start_unix_nano")
                window_end = _ns(item["window_end_unix_nano"], "window_end_unix_nano")
                if window_end <= window_start:
                    raise InvalidData("Transform window end must be later than start")
                window_id = uuid.uuid4()
                window = conn.execute(
                    """INSERT INTO observation_window(
                           observation_window_id,transform_run_id,replay_run_id,service_instance_id,
                           window_start_unix_nano,window_end_unix_nano
                       ) VALUES (%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (transform_run_id,service_instance_id,window_start_unix_nano,window_end_unix_nano)
                       DO NOTHING RETURNING observation_window_id""",
                    (window_id, transform_uuid, replay_uuid, instance["service_instance_id"], window_start, window_end),
                ).fetchone()
                if window:
                    window_id = window["observation_window_id"]
                else:
                    window_id = conn.execute(
                        """SELECT observation_window_id FROM observation_window
                           WHERE transform_run_id=%s AND service_instance_id=%s
                             AND window_start_unix_nano=%s AND window_end_unix_nano=%s""",
                        (transform_uuid, instance["service_instance_id"], window_start, window_end),
                    ).fetchone()["observation_window_id"]
                state = str(item["coverage_state"])
                reason = item.get("reason")
                provenance = dict(item.get("provenance") or {})
                conn.execute(
                    """INSERT INTO metric_coverage(
                           metric_coverage_id,transform_run_id,observation_window_id,derived_metric_definition_id,
                           coverage_state,reason,provenance
                       ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (transform_run_id,observation_window_id,derived_metric_definition_id)
                       DO UPDATE SET coverage_state=EXCLUDED.coverage_state,reason=EXCLUDED.reason,provenance=EXCLUDED.provenance""",
                    (uuid.uuid4(), transform_uuid, window_id, definition["derived_metric_definition_id"],
                     state, reason, Jsonb(provenance)),
                )
                value = item.get("value")
                if value is None:
                    continue
                value = float(value)
                if not math.isfinite(value):
                    raise InvalidData("Derived values must be finite")
                point = conn.execute(
                    """INSERT INTO derived_metric_point(
                           transform_run_id,observation_window_id,derived_metric_definition_id,value,provenance
                       ) VALUES (%s,%s,%s,%s,%s)
                       ON CONFLICT (transform_run_id,observation_window_id,derived_metric_definition_id)
                       DO NOTHING RETURNING derived_metric_point_id""",
                    (transform_uuid, window_id, definition["derived_metric_definition_id"], value, Jsonb(provenance)),
                ).fetchone()
                if not point:
                    existing = conn.execute(
                        """SELECT derived_metric_point_id,value,provenance FROM derived_metric_point
                           WHERE transform_run_id=%s AND observation_window_id=%s AND derived_metric_definition_id=%s""",
                        (transform_uuid, window_id, definition["derived_metric_definition_id"]),
                    ).fetchone()
                    if float(existing["value"]) != value or existing["provenance"] != provenance:
                        raise Conflict("Transform run contains a conflicting derived value for the same window")
                    point = existing
                for raw_id in item.get("source_raw_point_ids") or []:
                    try:
                        raw_id = int(raw_id)
                    except (TypeError, ValueError) as exc:
                        raise InvalidData("source_raw_point_ids must be integer raw point IDs") from exc
                    owner = conn.execute(
                        "SELECT replay_run_id FROM raw_metric_point WHERE raw_metric_point_id=%s", (raw_id,)
                    ).fetchone()
                    if not owner or owner["replay_run_id"] != replay_uuid:
                        raise InvalidData("Derived point lineage must reference raw points from the same replay")
                    conn.execute(
                        """INSERT INTO derived_point_source(derived_metric_point_id,raw_metric_point_id)
                           VALUES (%s,%s) ON CONFLICT DO NOTHING""",
                        (point["derived_metric_point_id"], raw_id),
                    )

    def finish_transform_run(
        self,
        transform_id: str | uuid.UUID,
        status: str = "complete",
        summary: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        transform_uuid = _uuid(transform_id)
        if status not in {"complete", "failed"}:
            raise InvalidData("finished transform status must be complete or failed")
        with connection(self.dsn) as conn:
            transform = conn.execute(
                """UPDATE transform_run SET status=%s,summary=%s,error=%s,completed_at=now()
                   WHERE transform_run_id=%s AND status='running' RETURNING *""",
                (status, Jsonb(summary or {}), error, transform_uuid),
            ).fetchone()
            if not transform:
                raise NotFound("Active transform run not found")
            replay_status = "processed" if status == "complete" else "ingested"
            conn.execute("UPDATE replay_run SET status=%s WHERE replay_run_id=%s", (replay_status, transform["replay_run_id"]))
        return self._plain_transform(transform)

    def _plain_transform(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "transform_run_id": str(row["transform_run_id"]),
            "replay_run_id": str(row["replay_run_id"]),
            "version": row["version"],
            "config": row["config"],
            "status": row["status"],
            "summary": row["summary"],
            "error": row["error"],
            "created_at": _iso(row["created_at"]),
            "completed_at": _iso(row["completed_at"]),
        }

    def list_services(self, replay_id: str | uuid.UUID) -> list[dict[str, Any]]:
        replay_uuid = _uuid(replay_id)
        with connection(self.dsn) as conn:
            self._replay_row(conn, replay_uuid)
            rows = conn.execute(
                """SELECT e.service_id,e.service_name,i.instance_name AS instance_id
                   FROM service_entity e JOIN service_instance i USING(service_id)
                   WHERE e.replay_run_id=%s ORDER BY e.service_name,i.instance_name""",
                (replay_uuid,),
            ).fetchall()
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            service_id = str(row["service_id"])
            service = grouped.setdefault(service_id, {"service_id": service_id, "service_name": row["service_name"], "instances": []})
            service["instances"].append({"instance_id": row["instance_id"], "instance_name": row["instance_id"]})
        return list(grouped.values())

    def get_ingestion_progress(
        self, replay_id: str | uuid.UUID, service_id: str | uuid.UUID, instance_id: str
    ) -> dict[str, Any]:
        replay_uuid, service_uuid = _uuid(replay_id), _uuid(service_id)
        with connection(self.dsn) as conn:
            instance = conn.execute(
                """SELECT i.service_instance_id
                   FROM service_instance i JOIN service_entity e USING(service_id)
                   WHERE i.replay_run_id=%s AND e.service_id=%s AND i.instance_name=%s""",
                (replay_uuid, service_uuid, instance_id),
            ).fetchone()
            if not instance:
                raise NotFound("Service instance does not belong to this replay/service")
            row = conn.execute(
                """SELECT count(p.raw_metric_point_id) AS raw_point_count,
                          count(DISTINCT p.ingest_batch_id) AS ingest_batch_count,
                          max(p.source_timestamp_unix_nano) AS latest_source_timestamp_unix_nano,
                          max(p.received_at) AS latest_received_at
                   FROM raw_metric_point p
                   JOIN metric_series s USING(metric_series_id)
                   WHERE p.replay_run_id=%s AND s.service_instance_id=%s""",
                (replay_uuid, instance["service_instance_id"]),
            ).fetchone()
        return {
            "replay_run_id": str(replay_uuid), "service_id": str(service_uuid),
            "instance_id": instance_id, "raw_point_count": int(row["raw_point_count"]),
            "ingest_batch_count": int(row["ingest_batch_count"]),
            "latest_source_timestamp_unix_nano": str(row["latest_source_timestamp_unix_nano"])
                if row["latest_source_timestamp_unix_nano"] is not None else None,
            "latest_received_at": _iso(row["latest_received_at"]),
        }

    def list_transforms(self, replay_id: str | uuid.UUID) -> dict[str, Any]:
        replay_uuid = _uuid(replay_id)
        with connection(self.dsn) as conn:
            self._replay_row(conn, replay_uuid)
            rows = conn.execute(
                """SELECT * FROM transform_run WHERE replay_run_id=%s
                   ORDER BY completed_at DESC NULLS LAST, transform_run_id DESC""",
                (replay_uuid,),
            ).fetchall()
        transforms = [self._plain_transform(row) for row in rows]
        preferred = next(
            (
                item["transform_run_id"]
                for item in transforms
                if item["status"] == "complete" and item["version"] == "counter-rates-60s-v1"
            ),
            None,
        )
        default = preferred or next(
            (item["transform_run_id"] for item in transforms if item["status"] == "complete"),
            None,
        )
        return {"transforms": transforms, "default_transform_run_id": default}

    def get_metrics(
        self,
        replay_id: str | uuid.UUID,
        service_id: str | uuid.UUID,
        instance_id: str,
        transform_id: str | uuid.UUID,
        from_unix_nano: int | None = None,
        to_unix_nano: int | None = None,
    ) -> dict[str, Any]:
        replay_uuid, service_uuid, transform_uuid = _uuid(replay_id), _uuid(service_id), _uuid(transform_id)
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid)
            transform = conn.execute(
                "SELECT * FROM transform_run WHERE transform_run_id=%s AND replay_run_id=%s",
                (transform_uuid, replay_uuid),
            ).fetchone()
            if not transform:
                raise NotFound("Transform run does not belong to this replay")
            if transform["status"] != "complete":
                raise Conflict("Only complete transform runs can be queried")
            instance = conn.execute(
                """SELECT i.service_instance_id,i.instance_name,e.service_id,e.service_name
                   FROM service_instance i JOIN service_entity e USING(service_id)
                   WHERE i.replay_run_id=%s AND e.service_id=%s AND i.instance_name=%s""",
                (replay_uuid, service_uuid, instance_id),
            ).fetchone()
            if not instance:
                raise NotFound("Service instance does not belong to this replay/service")
            start = _ns(from_unix_nano, "from_unix_nano") if from_unix_nano is not None else int(replay["display_start_unix_nano"])
            end = _ns(to_unix_nano, "to_unix_nano") if to_unix_nano is not None else int(replay["display_end_unix_nano"])
            if end <= start:
                raise InvalidData("to_unix_nano must be later than from_unix_nano")
            rows = conn.execute(
                """SELECT d.metric_name,d.unit,p.value,w.window_start_unix_nano,w.window_end_unix_nano,
                          c.coverage_state,c.reason,c.provenance AS coverage_provenance,
                          p.provenance AS point_provenance
                   FROM metric_coverage c
                   JOIN observation_window w USING(observation_window_id,transform_run_id)
                   JOIN derived_metric_definition d USING(derived_metric_definition_id)
                   LEFT JOIN derived_metric_point p
                     ON p.transform_run_id=c.transform_run_id
                    AND p.observation_window_id=c.observation_window_id
                    AND p.derived_metric_definition_id=c.derived_metric_definition_id
                   WHERE c.transform_run_id=%s AND w.service_instance_id=%s
                     AND w.window_end_unix_nano>%s AND w.window_start_unix_nano<%s
                   ORDER BY d.metric_name,w.window_start_unix_nano""",
                (transform_uuid, instance["service_instance_id"], start, end),
            ).fetchall()
        metrics = []
        for row in rows:
            provenance = dict(row["coverage_provenance"] or {})
            provenance.update(dict(row["point_provenance"] or {}))
            metrics.append({
                "metric_name": row["metric_name"],
                "value": float(row["value"]) if row["value"] is not None else None,
                "unit": row["unit"],
                "window_start_unix_nano": str(int(row["window_start_unix_nano"])),
                "window_end_unix_nano": str(int(row["window_end_unix_nano"])),
                "coverage_state": row["coverage_state"],
                "reason": row["reason"],
                "provenance": provenance,
            })
        return {
            "replay_run_id": str(replay_uuid), "transform_run_id": str(transform_uuid),
            "transform_version": transform["version"], "service_id": str(service_uuid),
            "service_name": instance["service_name"], "instance_id": instance_id,
            "metrics": metrics,
        }

    def get_raw_export(
        self,
        replay_id: str | uuid.UUID,
        service_id: str | uuid.UUID,
        instance_id: str,
        from_unix_nano: int | None = None,
        to_unix_nano: int | None = None,
    ) -> dict[str, Any]:
        """Read original persisted points for a replay/entity and display interval."""
        replay_uuid, service_uuid = _uuid(replay_id), _uuid(service_id)
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid)
            instance = conn.execute(
                """SELECT i.service_instance_id,i.instance_name,e.service_id,e.service_name
                   FROM service_instance i JOIN service_entity e USING(service_id)
                   WHERE i.replay_run_id=%s AND e.service_id=%s AND i.instance_name=%s""",
                (replay_uuid, service_uuid, instance_id),
            ).fetchone()
            if not instance:
                raise NotFound("Service instance does not belong to this replay/service")
            raw_start = int(replay["raw_start_unix_nano"])
            raw_end_exclusive = int(replay["raw_end_unix_nano"]) + 1
            start = _ns(from_unix_nano, "from_unix_nano") if from_unix_nano is not None else raw_start
            end = _ns(to_unix_nano, "to_unix_nano") if to_unix_nano is not None else raw_end_exclusive
            if end <= start:
                raise InvalidData("to_unix_nano must be later than from_unix_nano")
            if start < raw_start or end > raw_end_exclusive:
                raise InvalidData("Raw export interval must be inside the replay source interval")
            rows = conn.execute(
                """SELECT d.metric_name,d.unit,p.value_type,p.value_int,p.value_double,
                          p.source_timestamp_unix_nano,p.start_time_unix_nano,s.source_cmdb_id,
                          p.source_file_sha256,p.source_row_ordinal,p.resource_attributes,
                          p.scope_attributes,p.datapoint_attributes,s.metric_series_id
                   FROM raw_metric_point p
                   JOIN metric_series s USING(metric_series_id)
                   JOIN source_metric_definition d USING(source_metric_definition_id)
                   WHERE p.replay_run_id=%s AND s.service_instance_id=%s
                     AND p.source_timestamp_unix_nano >= %s AND p.source_timestamp_unix_nano < %s
                   ORDER BY p.source_timestamp_unix_nano,d.metric_name,s.source_cmdb_id,p.source_row_ordinal""",
                (replay_uuid, instance["service_instance_id"], start, end),
            ).fetchall()
        points = []
        for row in rows:
            points.append({
                "metric_name": row["metric_name"], "unit": row["unit"],
                "value_type": row["value_type"], "value": _typed_number(row["value_type"], row["value_int"], row["value_double"]),
                "time_unix_nano": str(int(row["source_timestamp_unix_nano"])),
                "start_time_unix_nano": str(int(row["start_time_unix_nano"])) if row["start_time_unix_nano"] is not None else "",
                "source_cmdb_id": row["source_cmdb_id"], "source_file_sha256": row["source_file_sha256"].strip(),
                "source_row_ordinal": int(row["source_row_ordinal"]), "metric_series_id": str(row["metric_series_id"]),
                "resource_attributes": row["resource_attributes"], "scope_attributes": row["scope_attributes"],
                "datapoint_attributes": row["datapoint_attributes"],
            })
        return {
            "replay_run_id": str(replay_uuid), "service_id": str(service_uuid),
            "service_name": instance["service_name"], "instance_id": instance["instance_name"],
            "from_unix_nano": str(start), "to_unix_nano": str(end), "points": points,
        }

    def list_events(
        self,
        replay_id: str | uuid.UUID,
        from_unix_nano: int | None = None,
        to_unix_nano: int | None = None,
    ) -> dict[str, Any]:
        replay_uuid = _uuid(replay_id)
        with connection(self.dsn) as conn:
            replay = self._replay_row(conn, replay_uuid)
            start = _ns(from_unix_nano, "from_unix_nano") if from_unix_nano is not None else int(replay["display_start_unix_nano"])
            end = _ns(to_unix_nano, "to_unix_nano") if to_unix_nano is not None else int(replay["display_end_unix_nano"])
            if end <= start:
                raise InvalidData("to_unix_nano must be later than from_unix_nano")
            rows = conn.execute(
                """SELECT g.ground_truth_event_id,g.event_type,g.failure_type,g.start_unix_nano,g.end_unix_nano,
                          i.instance_name AS instance_id,g.source_file_sha256,g.source_event_ordinal,e.service_name
                   FROM ground_truth_event g
                   JOIN service_instance i USING(service_instance_id)
                   JOIN service_entity e USING(service_id)
                   WHERE g.replay_run_id=%s AND g.end_unix_nano>%s AND g.start_unix_nano<%s
                   ORDER BY g.start_unix_nano,g.source_event_ordinal""",
                (replay_uuid, start, end),
            ).fetchall()
        events = [{
            "event_id": str(row["ground_truth_event_id"]),
            "event_kind": row["event_type"],
            "failure_type": row["failure_type"],
            "start_unix_nano": str(int(row["start_unix_nano"])),
            "end_unix_nano": str(int(row["end_unix_nano"])),
            "instance_id": row["instance_id"],
            "service_name": row["service_name"],
            "source_file_sha256": row["source_file_sha256"],
            "source_event_ordinal": int(row["source_event_ordinal"]),
        } for row in rows]
        return {"replay_run_id": str(replay_uuid), "events": events}
