"""Explicit live acceptance: API -> Collector -> PostgreSQL, without HTTP fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path

import httpx


def verify(base: str) -> dict:
    with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
        before = client.get("/api/v1/replays")
        before.raise_for_status()
        previous = {item["replay_run_id"] for item in before.json()["replays"]}
        key = str(uuid.uuid4())
        started = time.monotonic()
        response = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": key})
        assert response.status_code == 202, response.text
        first = response.json()
        initial_latency = time.monotonic() - started
        demo_id = first["demo_run_id"]
        repeated = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": key})
        assert repeated.status_code == 202 and repeated.json()["demo_run_id"] == demo_id
        conflict = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": str(uuid.uuid4())})
        assert conflict.status_code == 409 and conflict.json()["detail"]["demo_run_id"] == demo_id
        observations = []
        deadline = time.monotonic() + 600
        while True:
            state = client.get(f"/api/v1/demo-runs/{demo_id}")
            state.raise_for_status()
            state = state.json()
            progress = (state["completed_chunks"], state["raw_point_count"])
            if not observations or progress != (observations[-1]["completed_chunks"], observations[-1]["raw_point_count"]):
                observations.append(state)
                print(json.dumps({key: state[key] for key in ("status", "current_stage", "completed_chunks", "total_chunks", "raw_point_count")}), flush=True)
            if state["status"] in ("completed", "failed"):
                assert state["status"] == "completed", state
                break
            assert time.monotonic() < deadline, "Demonstration did not finish within its bounded test deadline"
            time.sleep(0.5)
        assert state["raw_point_count"] == state["expected_raw_point_count"] == 282
        assert state["completed_chunks"] == state["total_chunks"] == 12
        assert state["replay_run_id"] not in previous
        assert len(observations) >= 3, "Progress was not observed between milestones"
        assert all(left["raw_point_count"] <= right["raw_point_count"] for left, right in zip(observations, observations[1:]))
        finished_retry = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": key})
        assert finished_retry.status_code == 202 and finished_retry.json()["demo_run_id"] == demo_id
        replay_id = state["replay_run_id"]
        services = client.get(f"/api/v1/replays/{replay_id}/services").json()["services"]
        service = services[0]
        instance = service["instances"][0]["instance_id"]
        resolutions = {}
        for seconds, transform_id in ((15, state["latest_transform_run_id"]), (60, state["latest_transform_60s_run_id"])):
            metrics = client.get(f"/api/v1/replays/{replay_id}/services/{service['service_id']}/metrics",
                                 params={"instance_id": instance, "transform_run_id": transform_id})
            metrics.raise_for_status()
            points = metrics.json()["metrics"]
            resolutions[str(seconds)] = {"coverage_rows": len(points), "numeric_values": sum(point["value"] is not None for point in points),
                                         "sha256": hashlib.sha256(json.dumps(points, sort_keys=True).encode()).hexdigest()}
        assert resolutions["15"]["coverage_rows"] == 276 and resolutions["15"]["numeric_values"] == 207
        assert resolutions["60"]["coverage_rows"] == resolutions["60"]["numeric_values"] == 69
        events = client.get(f"/api/v1/replays/{replay_id}/events").json()["events"]
        assert len(events) == 1 and events[0]["event_kind"] == "injected_fault"
        after = {item["replay_run_id"] for item in client.get("/api/v1/replays").json()["replays"]}
        assert previous <= after, "An earlier replay was removed"
        assert client.get("/api/v1/demo-runs/active").json() == {"demo_run": None}
        return {"status": "passed", "transport": "API thread -> OTLP/HTTP Protobuf -> configured Collector -> PostgreSQL",
                "initial_http_202_seconds": initial_latency, "demo_run": state, "observed_progress": observations,
                "resolutions": resolutions, "previous_replays_preserved": len(previous), "idempotency_after_completion": True,
                "concurrent_post_status": conflict.status_code}


def raw_progress(client: httpx.Client, replay_id: str) -> dict:
    service = client.get(f"/api/v1/replays/{replay_id}/services").json()["services"][0]
    response = client.get(f"/api/v1/replays/{replay_id}/services/{service['service_id']}/progress",
                          params={"instance_id": service["instances"][0]["instance_id"]})
    response.raise_for_status()
    return response.json()


def prepare_restart(base: str, acceptance: dict) -> dict:
    with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
        previous = [item["replay_run_id"] for item in client.get("/api/v1/replays").json()["replays"]]
        response = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": str(uuid.uuid4())})
        assert response.status_code == 202, response.text
        created = response.json()
        deadline = time.monotonic() + 180
        while True:
            state = client.get(f"/api/v1/demo-runs/{created['demo_run_id']}").json()
            assert state["status"] != "failed", state
            if state["replay_run_id"] and state["latest_transform_run_id"]:
                break
            assert time.monotonic() < deadline
            time.sleep(0.2)
        assert state["replay_run_id"] not in previous
        assert state["replay_run_id"] != acceptance["demo_run"]["replay_run_id"]
        return {"stage": "ready_for_api_restart", "previous_replay_ids": previous,
                "completed_acceptance": acceptance, "interrupted_candidate": state,
                "raw_before": raw_progress(client, state["replay_run_id"])}


def check_restart(base: str, prepared: dict) -> dict:
    with httpx.Client(base_url=base, timeout=30, trust_env=False) as client:
        old = prepared["interrupted_candidate"]
        state = client.get(f"/api/v1/demo-runs/{old['demo_run_id']}").json()
        assert state["status"] == "failed" and state["error_code"] == "interrupted", state
        assert client.get("/api/v1/demo-runs/active").json() == {"demo_run": None}
        after_ids = {item["replay_run_id"] for item in client.get("/api/v1/replays").json()["replays"]}
        assert set(prepared["previous_replay_ids"]) <= after_ids
        assert old["replay_run_id"] in after_ids
        after_raw = raw_progress(client, old["replay_run_id"])
        assert after_raw["raw_point_count"] >= prepared["raw_before"]["raw_point_count"] > 0
        completed = prepared["completed_acceptance"]
        first = completed["demo_run"]
        assert client.get(f"/api/v1/demo-runs/{first['demo_run_id']}").json()["status"] == "completed"
        service = client.get(f"/api/v1/replays/{first['replay_run_id']}/services").json()["services"][0]
        for seconds, transform_id in (("15", first["latest_transform_run_id"]), ("60", first["latest_transform_60s_run_id"])):
            points = client.get(f"/api/v1/replays/{first['replay_run_id']}/services/{service['service_id']}/metrics",
                params={"instance_id": service["instances"][0]["instance_id"], "transform_run_id": transform_id}).json()["metrics"]
            assert hashlib.sha256(json.dumps(points, sort_keys=True).encode()).hexdigest() == completed["resolutions"][seconds]["sha256"]
        return {"status": "passed", "api_restart_interrupted_active_job": True,
                "all_previous_replay_ids_preserved": True, "previous_replay_count": len(prepared["previous_replay_ids"]),
                "after_replay_count": len(after_ids), "completed_demo_run_id": first["demo_run_id"],
                "completed_replay_run_id": first["replay_run_id"], "completed_snapshot_hashes_unchanged": True,
                "interrupted_demo": state, "partial_raw_after_restart": after_raw}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--mode", choices=("run", "prepare-restart", "check-restart"), default="run")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "run":
        result = verify(args.base_url)
    else:
        previous = json.loads(args.input.read_text(encoding="utf-8"))
        operation = prepare_restart if args.mode == "prepare-restart" else check_restart
        result = operation(args.base_url, previous)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
