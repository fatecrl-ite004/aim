"""Real HTTP/PostgreSQL acceptance checks; output contains metadata, not source rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import psycopg
from dotenv import load_dotenv
from google.rpc.status_pb2 import Status

from aim.dataset import INSTANCE, SERVICE, load_cut, load_ground_truth
from aim.replay import build_request, send_replay, verify_persisted
from aim.repository import Repository
from aim.transform import run_transform

ROOT = Path(__file__).resolve().parents[1]


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def request_json(client: httpx.Client, path: str) -> dict[str, Any]:
    response = client.get(path)
    response.raise_for_status()
    return response.json()


def metrics_path(client: httpx.Client, replay_id: str, transform_id: str) -> str:
    services = request_json(client, f"/api/v1/replays/{replay_id}/services")["services"]
    service = next(service for service in services if service["service_name"] == SERVICE)
    instance = next(instance for instance in service["instances"] if instance["instance_name"] == INSTANCE)
    return f"/api/v1/replays/{replay_id}/services/{service['service_id']}/metrics?instance_id={instance['instance_id']}&transform_run_id={transform_id}"


def take_snapshot(replay_id: str, transform_id: str) -> dict[str, Any]:
    repository = Repository()
    with httpx.Client(base_url=os.environ.get("AIM_API_URL", "http://127.0.0.1:8000"), timeout=30, trust_env=False) as client:
        readiness = request_json(client, "/health/ready")
        metrics = request_json(client, metrics_path(client, replay_id, transform_id))["metrics"]
        events = request_json(client, f"/api/v1/replays/{replay_id}/events")["events"]
        transforms = request_json(client, f"/api/v1/replays/{replay_id}/transforms")
    raw = repository.get_raw_points(replay_id)
    raw_comparable = sorted(
        [(str(point["id"]), str(point["series_id"]), point["metric_name"], point["source_cmdb_id"], int(point["time_unix_nano"]), point["value"], point["source_file_sha256"], point["source_row_ordinal"]) for point in raw],
        key=lambda row: (row[2], row[4], row[-1]),
    )
    with psycopg.connect(os.environ["AIM_DATABASE_URL"]) as connection:
        postgres_started_at, postgres_version = connection.execute("SELECT pg_postmaster_start_time(), version()").fetchone()
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(), "replay_run_id": replay_id, "transform_run_id": transform_id,
        "postgres_started_at": postgres_started_at.isoformat(), "postgres_version": postgres_version,
        "raw_points": len(raw), "raw_series": len({str(point["series_id"]) for point in raw}),
        "coverage_rows": len(metrics), "numeric_derived_points": sum(row["value"] is not None for row in metrics),
        "ground_truth_events": len(events), "raw_sha256": digest(raw_comparable),
        "metrics_sha256": digest(metrics), "events_sha256": digest(events),
        "default_transform_run_id": transforms["default_transform_run_id"], "readiness": readiness,
    }


def _assert_otlp_error(response: httpx.Response, status_code: int) -> None:
    assert response.status_code == status_code, f"Expected HTTP {status_code}, got {response.status_code}: {response.text[:300]}"
    assert response.headers["content-type"].split(";")[0] == "application/x-protobuf"
    status = Status.FromString(response.content)
    assert status.code != 0 and status.message


def run_acceptance() -> dict[str, Any]:
    repository = Repository()
    cut = load_cut(Path(os.environ["AIM_DATASET_ROOT"]))
    base = os.environ.get("AIM_API_URL", "http://127.0.0.1:8000")
    with httpx.Client(base_url=base, timeout=60, trust_env=False) as client:
        request_json(client, "/health/live")
        request_json(client, "/health/ready")
        receipt = send_replay(cut, base)
        replay_id = receipt["replay_run_id"]
        raw_verification = verify_persisted(cut, repository.get_raw_points(replay_id))
        assert len({point["series_id"] for point in repository.get_raw_points(replay_id)}) == 3, "Source ordinals incorrectly split logical series"
        assert request_json(client, f"/api/v1/replays/{replay_id}/events")["events"] == [], "Labels entered with OTLP metric data"

        # Identical retry may record another receipt; it may not duplicate raw points.
        retry = send_replay(cut, base, replay_id)
        assert retry["payload_sha256"] == receipt["payload_sha256"]
        verify_persisted(cut, repository.get_raw_points(replay_id))
        headers = {"Content-Type": "application/x-protobuf"}
        _assert_otlp_error(client.post("/v1/metrics", content=b"\xff", headers=headers), 400)

        # A mixed-profile batch must reject the whole message, including a new point.
        mixed = build_request(cut, replay_id)
        sample = mixed.resource_metrics[0].scope_metrics[0].metrics[0].sum.data_points.add()
        sample.CopyFrom(mixed.resource_metrics[0].scope_metrics[0].metrics[0].sum.data_points[0])
        for attribute in sample.attributes:
            if attribute.key == "aim.source.row_ordinal":
                attribute.value.int_value = 999_999_999
        mixed.resource_metrics[1].scope_metrics[0].metrics[0].unit = "unsupported-unit"
        _assert_otlp_error(client.post("/v1/metrics", content=mixed.SerializeToString(), headers=headers), 400)
        verify_persisted(cut, repository.get_raw_points(replay_id))

        # Reusing a stable source identity with a changed value is a conflict.
        conflict = build_request(cut, replay_id)
        conflict.resource_metrics[0].scope_metrics[0].metrics[0].sum.data_points[0].as_double += 0.5
        _assert_otlp_error(client.post("/v1/metrics", content=conflict.SerializeToString(), headers=headers), 409)
        verify_persisted(cut, repository.get_raw_points(replay_id))

        gt_sha, events = load_ground_truth(Path(os.environ["AIM_DATASET_ROOT"]))
        assert gt_sha == next(file["sha256"] for file in cut.source_manifest["files"] if file["role"] == "ground_truth")
        repository.import_ground_truth(replay_id, events)
        repository.import_ground_truth(replay_id, events)
        saved_events = request_json(client, f"/api/v1/replays/{replay_id}/events")["events"]
        assert len(saved_events) == 1 and saved_events[0]["event_kind"] == "injected_fault"

        first = run_transform(repository, replay_id)
        second = run_transform(repository, replay_id)
        assert first["transform_run_id"] != second["transform_run_id"]
        assert first["summary"] == second["summary"]
        first_metrics = request_json(client, metrics_path(client, replay_id, first["transform_run_id"]))["metrics"]
        second_metrics = request_json(client, metrics_path(client, replay_id, second["transform_run_id"]))["metrics"]
        assert len(first_metrics) == len(second_metrics) == 92 * 3
        # API rows should be deterministic apart from implementation identifiers.
        keys = ("metric_name", "value", "unit", "window_start_unix_nano", "window_end_unix_nano", "coverage_state", "reason")
        comparable = lambda rows: sorted([tuple(row.get(key) for key in keys) for row in rows], key=lambda row: (row[0], row[3]))
        assert comparable(first_metrics) == comparable(second_metrics)
        assert all(isinstance(row["window_start_unix_nano"], str) for row in second_metrics)
        assert any(row["value"] is None and row["reason"] == "no_observed_increment" for row in second_metrics)
        assert not any(row["metric_name"] in ("error_rate", "p95", "p99") for row in second_metrics)
        transforms = request_json(client, f"/api/v1/replays/{replay_id}/transforms")
        assert transforms["default_transform_run_id"] == second["transform_run_id"]
        # Explicit transform ownership: a different replay's run cannot leak data.
        another = client.post("/api/v1/replays", json=cut.replay_payload())
        another.raise_for_status()
        wrong = client.get(metrics_path(client, another.json()["replay_run_id"], second["transform_run_id"]))
        assert wrong.status_code in (400, 404, 422)
    return {
        "executed_at": datetime.now(timezone.utc).isoformat(), "status": "passed",
        "replay_run_id": replay_id, "transform_run_id": second["transform_run_id"],
        "source_manifest_sha256": cut.source_manifest["manifest_sha256"], "otlp_receipt": receipt,
        "raw_verification": raw_verification, "transform": second,
        "checks": ["post_commit_raw_visible", "282_exact_source_values", "3_logical_series", "identical_retry_idempotent", "malformed_protobuf_status", "atomic_mixed_batch_rejection", "conflicting_retry_rollback", "separate_idempotent_ground_truth", "versioned_repeatable_postgresql_batch", "276_coverage_rows", "explicit_transform_ownership", "nanoseconds_json_strings", "no_observed_increment_latency_null"],
        "snapshot": take_snapshot(replay_id, second["transform_run_id"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("run", "snapshot", "compare"))
    parser.add_argument("--replay-id")
    parser.add_argument("--transform-id")
    parser.add_argument("--before", type=Path)
    parser.add_argument("--after", type=Path)
    parser.add_argument("--require-db-restart", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env.v1")
    if args.mode == "run":
        result = run_acceptance()
    elif args.mode == "snapshot":
        result = take_snapshot(args.replay_id, args.transform_id)
    else:
        before = json.loads(args.before.read_text(encoding="utf-8-sig"))
        after = json.loads(args.after.read_text(encoding="utf-8-sig"))
        for key in ("replay_run_id", "transform_run_id", "raw_points", "raw_series", "coverage_rows", "numeric_derived_points", "ground_truth_events", "raw_sha256", "metrics_sha256", "events_sha256"):
            assert before[key] == after[key], f"Persistence mismatch after restart: {key}"
        restarted = before["postgres_started_at"] != after["postgres_started_at"]
        if args.require_db_restart:
            assert restarted, "Database restart was not demonstrated"
        result = {"status": "passed", "postgres_restart_observed": restarted, "before": before, "after": after}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
