"""JSON control/read API for the local historical replay journey."""

from __future__ import annotations

import logging
import csv
import io
import json
from typing import Any, Callable
from uuid import UUID

import psycopg
from fastapi import APIRouter, HTTPException, Query, Response

from .repository import Conflict, InvalidData, NotFound, Repository

router = APIRouter(prefix="/api/v1", tags=["historical replay"])
logger = logging.getLogger(__name__)


def _call(operation: Callable[[], Any]) -> Any:
    try:
        return operation()
    except NotFound as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidData as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Conflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except psycopg.Error as error:
        logger.error("PostgreSQL operation failed: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="PostgreSQL is unavailable or the schema is not ready") from error


def _json_replay(replay: dict[str, Any]) -> dict[str, Any]:
    return {key: str(value) if key.endswith("_unix_nano") and value is not None else value for key, value in replay.items()}


def _csv_response(filename: str, columns: list[str], rows: list[dict[str, Any]]) -> Response:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore", lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=output.getvalue(), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )


@router.post("/replays", status_code=201)
def create_replay(payload: dict[str, Any]) -> dict[str, Any]:
    return _json_replay(_call(lambda: Repository().create_replay(payload)))


@router.get("/replays")
def list_replays() -> dict[str, Any]:
    return {"replays": [_json_replay(replay) for replay in _call(lambda: Repository().list_replays())]}


@router.get("/replays/{replay_run_id}/services")
def list_services(replay_run_id: UUID) -> dict[str, Any]:
    return {"replay_run_id": str(replay_run_id), "services": _call(lambda: Repository().list_services(str(replay_run_id)))}


@router.get("/replays/{replay_run_id}/transforms")
def list_transforms(replay_run_id: UUID) -> dict[str, Any]:
    result = _call(lambda: Repository().list_transforms(str(replay_run_id)))
    for transform in result["transforms"]:
        if transform["status"] == "complete":
            transform["status"] = "completed"
    return {"replay_run_id": str(replay_run_id), **result}


@router.get("/replays/{replay_run_id}/services/{service_id}/metrics")
def read_metrics(
    replay_run_id: UUID,
    service_id: UUID,
    instance_id: str = Query(min_length=1, max_length=200),
    transform_run_id: UUID = Query(),
    from_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
    to_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
) -> dict[str, Any]:
    return _call(lambda: Repository().get_metrics(
        str(replay_run_id), str(service_id), instance_id, str(transform_run_id),
        int(from_unix_nano) if from_unix_nano is not None else None,
        int(to_unix_nano) if to_unix_nano is not None else None,
    ))


@router.get("/replays/{replay_run_id}/services/{service_id}/progress")
def read_ingestion_progress(
    replay_run_id: UUID,
    service_id: UUID,
    instance_id: str = Query(min_length=1, max_length=200),
) -> dict[str, Any]:
    return _call(lambda: Repository().get_ingestion_progress(
        str(replay_run_id), str(service_id), instance_id,
    ))


@router.get("/replays/{replay_run_id}/services/{service_id}/export/raw.csv")
def export_raw_points(
    replay_run_id: UUID,
    service_id: UUID,
    instance_id: str = Query(min_length=1, max_length=200),
    from_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
    to_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
) -> Response:
    result = _call(lambda: Repository().get_raw_export(
        str(replay_run_id), str(service_id), instance_id,
        int(from_unix_nano) if from_unix_nano is not None else None,
        int(to_unix_nano) if to_unix_nano is not None else None,
    ))
    rows = [{
        "replay_run_id": result["replay_run_id"], "service_id": result["service_id"],
        "service_name": result["service_name"], "instance_id": result["instance_id"],
        "from_unix_nano": result["from_unix_nano"], "to_unix_nano": result["to_unix_nano"], **point,
        "resource_attributes": json.dumps(point["resource_attributes"], sort_keys=True, ensure_ascii=False),
        "scope_attributes": json.dumps(point["scope_attributes"], sort_keys=True, ensure_ascii=False),
        "datapoint_attributes": json.dumps(point["datapoint_attributes"], sort_keys=True, ensure_ascii=False),
    } for point in result["points"]]
    columns = ["replay_run_id", "service_id", "service_name", "instance_id", "from_unix_nano", "to_unix_nano",
               "metric_name", "unit", "value_type", "value", "time_unix_nano", "start_time_unix_nano",
               "source_cmdb_id", "source_file_sha256", "source_row_ordinal", "metric_series_id",
               "resource_attributes", "scope_attributes", "datapoint_attributes"]
    return _csv_response("aim-raw-points.csv", columns, rows)


@router.get("/replays/{replay_run_id}/services/{service_id}/export/derived.csv")
def export_derived_metrics(
    replay_run_id: UUID,
    service_id: UUID,
    instance_id: str = Query(min_length=1, max_length=200),
    transform_run_id: UUID = Query(),
    from_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
    to_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
) -> Response:
    result = _call(lambda: Repository().get_metrics(
        str(replay_run_id), str(service_id), instance_id, str(transform_run_id),
        int(from_unix_nano) if from_unix_nano is not None else None,
        int(to_unix_nano) if to_unix_nano is not None else None,
    ))
    rows = [{
        "replay_run_id": result["replay_run_id"], "transform_run_id": result["transform_run_id"],
        "transform_version": result["transform_version"], "service_id": result["service_id"],
        "service_name": result["service_name"], "instance_id": result["instance_id"],
        **point, "provenance": json.dumps(point["provenance"], sort_keys=True, ensure_ascii=False),
    } for point in result["metrics"]]
    columns = ["replay_run_id", "transform_run_id", "transform_version", "service_id", "service_name", "instance_id",
               "metric_name", "unit", "value", "window_start_unix_nano", "window_end_unix_nano",
               "coverage_state", "reason", "provenance"]
    return _csv_response("aim-derived-metrics.csv", columns, rows)


@router.get("/replays/{replay_run_id}/events")
def list_events(
    replay_run_id: UUID,
    from_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
    to_unix_nano: str | None = Query(default=None, pattern=r"^\d{1,20}$"),
) -> dict[str, Any]:
    return _call(lambda: Repository().list_events(
        str(replay_run_id),
        int(from_unix_nano) if from_unix_nano is not None else None,
        int(to_unix_nano) if to_unix_nano is not None else None,
    ))
