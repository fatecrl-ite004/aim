from __future__ import annotations

import threading
import time
import uuid

import pytest
import httpx
from fastapi.testclient import TestClient

from aim import demo_api, demo_runs
from aim.demo_runs import DemoBusy, DemoService, DemoUnavailable
from aim.main import app
from aim import progressive


class MemoryStore:
    def __init__(self):
        self.rows = {}

    def by_key(self, key):
        return next((dict(row) for row in self.rows.values() if row["key"] == key), None)

    def list(self, active_only=False):
        return [dict(row) for row in self.rows.values() if not active_only or row["status"] in demo_runs.ACTIVE]

    def reconcile(self):
        for row in self.rows.values():
            if row["status"] in demo_runs.ACTIVE:
                row.update(status="failed", error_code="interrupted")

    def create(self, key):
        row = {"demo_run_id": str(uuid.uuid4()), "key": key, "replay_run_id": None, "status": "queued"}
        self.rows[row["demo_run_id"]] = row
        return dict(row)

    def update(self, demo_id, *, progress=None, status="running", **fields):
        self.rows[demo_id].update(progress or {})
        self.rows[demo_id].update(fields, status=status)

    def get(self, demo_id):
        return dict(self.rows[demo_id])


@pytest.fixture
def configured(monkeypatch, tmp_path):
    (tmp_path / "Case-1" / "Case-1").mkdir(parents=True)
    monkeypatch.setenv("AIM_DATASET_ROOT", str(tmp_path))
    monkeypatch.setenv("AIM_DEMO_PAUSE_SECONDS", "0")
    monkeypatch.setenv("AIM_DEMO_INITIAL_PAUSE_SECONDS", "0")
    held = threading.Lock()

    class Guard:
        def close(self):
            held.release()

    monkeypatch.setattr(demo_runs, "acquire_guard", lambda: Guard() if held.acquire(blocking=False) else None)
    return held


def wait_until(predicate):
    deadline = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < deadline, "Background demonstration did not finish"
        time.sleep(0.01)


def test_single_concurrency_idempotency_and_new_history(configured, monkeypatch):
    store = MemoryStore()
    service = DemoService(store)
    entered, release = threading.Event(), threading.Event()
    identifiers = []

    def runner(**config):
        replay_id = str(uuid.uuid4())
        identifiers.append(replay_id)
        config["on_progress"]({"replay_run_id": replay_id, "completed_chunks": 1, "raw_point_count": 24})
        entered.set()
        assert release.wait(3)
        return {"replay_run_id": replay_id, "chunk_count": 12, "source_point_count": 282,
                "final_transform": {"transform_run_id": str(uuid.uuid4())},
                "final_transform_60s": {"transform_run_id": str(uuid.uuid4())}}

    monkeypatch.setattr(demo_runs, "run_progressive", runner)
    key = str(uuid.uuid4())
    first = service.start(key)
    assert first["status"] == "queued"
    assert entered.wait(3)
    same = service.start(key)
    assert same["demo_run_id"] == first["demo_run_id"]
    with pytest.raises(DemoBusy) as busy:
        service.start(str(uuid.uuid4()))
    assert busy.value.active["demo_run_id"] == first["demo_run_id"]
    assert service.store.get(first["demo_run_id"])["raw_point_count"] == 24
    release.set()
    wait_until(lambda: not configured.locked())
    assert service.start(key)["status"] == "completed"
    second = service.start(str(uuid.uuid4()))
    wait_until(lambda: not configured.locked())
    assert len(store.rows) == 2
    assert second["demo_run_id"] != first["demo_run_id"]
    assert identifiers[0] != identifiers[1]


def test_failure_is_durable_sanitized_and_releases_slot(configured, monkeypatch):
    service = DemoService(MemoryStore())

    def fail(**config):
        raise ValueError("private-file-path-or-secret")

    monkeypatch.setattr(demo_runs, "run_progressive", fail)
    created = service.start()
    wait_until(lambda: not configured.locked())
    failed = service.store.get(created["demo_run_id"])
    assert failed["status"] == "failed"
    assert failed["error_code"] == "source_validation_failed"
    assert "private-file-path-or-secret" not in failed["message"]


def test_restart_reconciliation_requires_free_global_guard(configured):
    store = MemoryStore()
    pending = store.create(str(uuid.uuid4()))
    configured.acquire()
    DemoService(store).recover_interrupted()
    assert store.get(pending["demo_run_id"])["status"] == "queued"
    configured.release()
    DemoService(store).recover_interrupted()
    assert store.get(pending["demo_run_id"])["error_code"] == "interrupted"


def test_thread_start_failure_does_not_leave_a_queued_orphan(configured, monkeypatch):
    store = MemoryStore()
    service = DemoService(store)

    def fail_to_start(self):
        raise RuntimeError("thread unavailable")

    monkeypatch.setattr(threading.Thread, "start", fail_to_start)
    key = str(uuid.uuid4())
    with pytest.raises(RuntimeError, match="thread unavailable"):
        service.start(key)
    assert not configured.locked()
    assert store.by_key(key)["status"] == "failed"
    assert store.by_key(key)["error_code"] == "worker_start_failed"


def test_server_configuration_rejects_missing_source_and_invalid_pacing(monkeypatch, tmp_path):
    monkeypatch.setenv("AIM_DATASET_ROOT", str(tmp_path))
    with pytest.raises(DemoUnavailable):
        demo_runs._configuration()
    (tmp_path / "Case-1" / "Case-1").mkdir(parents=True)
    monkeypatch.setenv("AIM_DEMO_PAUSE_SECONDS", "nan")
    with pytest.raises(DemoUnavailable):
        demo_runs._configuration()


def test_http_contract_forbids_commands_and_accepts_idempotency_header(monkeypatch):
    seen = []

    class StubService:
        def start(self, key):
            seen.append(key)
            return {"demo_run_id": str(uuid.uuid4()), "status": "queued", "replay_run_id": None}

    monkeypatch.setattr(demo_api, "DemoService", StubService)
    client = TestClient(app)
    key = str(uuid.uuid4())
    assert client.post("/api/v1/demo-runs", json={"command": "anything"}).status_code == 422
    assert client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": "not-a-uuid"}).status_code == 422
    accepted = client.post("/api/v1/demo-runs", json={}, headers={"Idempotency-Key": key})
    assert accepted.status_code == 202
    assert seen == [key]


def test_http_busy_response_identifies_active_demo(monkeypatch):
    active = {"demo_run_id": str(uuid.uuid4()), "replay_run_id": str(uuid.uuid4())}

    class StubService:
        def start(self, key):
            raise DemoBusy(active)

    monkeypatch.setattr(demo_api, "DemoService", StubService)
    response = TestClient(app).post("/api/v1/demo-runs", json={})
    assert response.status_code == 409
    assert response.json()["detail"]["demo_run_id"] == active["demo_run_id"]


def test_otlp_slice_retries_only_transient_failures(monkeypatch):
    attempts = []
    request = httpx.Request("POST", "http://collector/v1/metrics")

    def transient(*args, **kwargs):
        attempts.append((args, kwargs))
        if len(attempts) < 3:
            raise httpx.HTTPStatusError("not ready", request=request, response=httpx.Response(503, request=request))
        return {"accepted": True}

    monkeypatch.setattr(progressive, "send_replay", transient)
    monkeypatch.setattr(progressive.time, "sleep", lambda seconds: None)
    assert progressive._send_slice("cut", "api", "same-replay", 0, 8) == {"accepted": True}
    assert len(attempts) == 3 and attempts[0] == attempts[-1]
    attempts.clear()

    def permanent(*args, **kwargs):
        attempts.append(args)
        raise httpx.HTTPStatusError("invalid profile", request=request, response=httpx.Response(400, request=request))

    monkeypatch.setattr(progressive, "send_replay", permanent)
    with pytest.raises(httpx.HTTPStatusError):
        progressive._send_slice("cut", "api", "same-replay", 0, 8)
    assert len(attempts) == 1


def test_source_cache_reuses_only_unchanged_file_signature(monkeypatch):
    loaded = []
    state = {"signature": (("source.csv", 100, 1),)}
    monkeypatch.setattr(progressive, "_source_signature", lambda root: state["signature"])
    monkeypatch.setattr(progressive, "load_cut", lambda root: loaded.append(root) or object())
    progressive._cached_cut.cache_clear()
    try:
        first = progressive._cached_cut("source-root", state["signature"])
        assert progressive._cached_cut("source-root", state["signature"]) is first
        assert len(loaded) == 1
        state["signature"] = (("source.csv", 101, 2),)
        assert progressive._cached_cut("source-root", state["signature"]) is not first
        assert len(loaded) == 2
    finally:
        progressive._cached_cut.cache_clear()


def test_postgresql_demo_state_and_interruption_are_durable():
    from aim.db import connection
    try:
        with connection() as conn:
            available = conn.execute("SELECT to_regclass('public.demo_run') AS demo_table").fetchone()["demo_table"]
    except Exception:
        pytest.skip("PostgreSQL unavailable")
    if not available:
        pytest.skip("Apply migration002_demo_runs.sql first")
    guard = demo_runs.acquire_guard()
    if guard is None:
        pytest.skip("A real demonstration is currently running")
    created = None
    try:
        store = demo_runs.DemoStore()
        # Holding the global lock makes reconciliation safe relative to real jobs.
        store.reconcile()
        key = str(uuid.uuid4())
        created = store.create(key)
        store.update(created["demo_run_id"], progress={"raw_point_count": 24, "completed_chunks": 1})
        reconnected = demo_runs.DemoStore().by_key(key)
        assert reconnected["demo_run_id"] == created["demo_run_id"]
        assert reconnected["status"] == "running"
        assert reconnected["raw_point_count"] == 24
        store.reconcile()
        interrupted = demo_runs.DemoStore().get(created["demo_run_id"])
        assert interrupted["status"] == "failed" and interrupted["error_code"] == "interrupted"
        assert interrupted["raw_point_count"] == 24
    finally:
        if created:
            with connection() as conn:
                conn.execute("DELETE FROM demo_run WHERE demo_run_id=%s", (uuid.UUID(created["demo_run_id"]),))
        guard.close()
