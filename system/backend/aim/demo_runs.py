"""Durable, single-concurrency local demonstration jobs. No shell execution."""

from __future__ import annotations

import logging
import math
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import psycopg
from psycopg.types.json import Jsonb

from .db import connect, connection
from .progressive import run_progressive
from .repository import NotFound

logger = logging.getLogger(__name__)
LOCK_NAMESPACE, LOCK_ID = 1095322948, 1
ACTIVE = {"queued", "running"}


class DemoUnavailable(RuntimeError):
    pass


class DemoBusy(RuntimeError):
    def __init__(self, active: dict[str, Any] | None):
        self.active = active


def _plain(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "demo_run_id": str(row["demo_run_id"]),
        "replay_run_id": str(row["replay_run_id"]) if row["replay_run_id"] else None,
        "status": row["status"],
        "current_stage": "queued", "total_chunks": 0, "completed_chunks": 0,
        "raw_point_count": 0, "expected_raw_point_count": 0,
        "latest_transform_run_id": None, "latest_transform_60s_run_id": None,
        "watermark_unix_nano": None, **row["progress"],
        "error_code": row["error_code"], "message": row["error_message"],
        **{key: row[key].isoformat() if row[key] else None for key in ("created_at", "started_at", "completed_at")},
    }


class DemoStore:
    def get(self, demo_id: str) -> dict[str, Any]:
        with connection() as conn:
            row = conn.execute("SELECT * FROM demo_run WHERE demo_run_id=%s", (uuid.UUID(demo_id),)).fetchone()
        if not row:
            raise NotFound("Demonstration run not found")
        return _plain(row)

    def by_key(self, key: str) -> dict[str, Any] | None:
        with connection() as conn:
            row = conn.execute("SELECT * FROM demo_run WHERE idempotency_key=%s", (uuid.UUID(key),)).fetchone()
        return _plain(row) if row else None

    def list(self, active_only: bool = False) -> list[dict[str, Any]]:
        predicate = " WHERE status IN ('queued','running')" if active_only else ""
        with connection() as conn:
            rows = conn.execute(f"SELECT * FROM demo_run{predicate} ORDER BY created_at DESC LIMIT 50").fetchall()
        return [_plain(row) for row in rows]

    def reconcile(self) -> None:
        with connection() as conn:
            conn.execute("""UPDATE demo_run SET status='failed',error_code='interrupted',
                error_message='A execução foi interrompida pelo reinício do processo. O histórico foi preservado.',
                progress=progress || '{"current_stage":"interrupted"}'::jsonb,completed_at=now()
                WHERE status IN ('queued','running')""")

    def create(self, key: str) -> dict[str, Any]:
        with connection() as conn:
            row = conn.execute("INSERT INTO demo_run(demo_run_id,idempotency_key,status) VALUES (%s,%s,'queued') RETURNING *",
                               (uuid.uuid4(), uuid.UUID(key))).fetchone()
        return _plain(row)

    def update(self, demo_id: str, *, progress: dict[str, Any] | None = None,
               status: str = "running", error_code: str | None = None, message: str | None = None) -> None:
        progress = dict(progress or {})
        replay_id = progress.pop("replay_run_id", None)
        with connection() as conn:
            conn.execute("""UPDATE demo_run SET status=%s,progress=progress || %s,
                replay_run_id=COALESCE(%s,replay_run_id),error_code=%s,error_message=%s,
                started_at=CASE WHEN %s='running' THEN COALESCE(started_at,now()) ELSE started_at END,
                completed_at=CASE WHEN %s IN ('completed','failed') THEN now() ELSE completed_at END
                WHERE demo_run_id=%s""",
                (status, Jsonb(progress), uuid.UUID(replay_id) if replay_id else None, error_code, message, status, status, uuid.UUID(demo_id)))


def acquire_guard():
    conn = connect()
    conn.autocommit = True
    try:
        locked = conn.execute("SELECT pg_try_advisory_lock(%s,%s) AS locked", (LOCK_NAMESPACE, LOCK_ID)).fetchone()["locked"]
        if locked:
            return conn
    except Exception:
        conn.close()
        raise
    conn.close()
    return None


def _configuration() -> dict[str, Any]:
    source = os.environ.get("AIM_DATASET_ROOT", "")
    root = Path(source) if source else None
    if root is None or not (root / "Case-1" / "Case-1").is_dir():
        raise DemoUnavailable("O dataset local não está configurado no servidor. Verifique AIM_DATASET_ROOT e o volume de leitura.")
    api_url = os.environ.get("AIM_DEMO_API_URL", "http://127.0.0.1:8000")
    endpoint = os.environ.get("AIM_OTLP_METRICS_ENDPOINT", f"{api_url.rstrip('/')}/v1/metrics")
    for url in (api_url, endpoint):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            raise DemoUnavailable("A configuração de transporte da demonstração é inválida no servidor.")
    try:
        chunk = int(os.environ.get("AIM_DEMO_CHUNK_TIMESTAMPS", "8"))
        pause = float(os.environ.get("AIM_DEMO_PAUSE_SECONDS", "3"))
        initial = float(os.environ.get("AIM_DEMO_INITIAL_PAUSE_SECONDS", "3"))
        if not 3 <= chunk <= 94 or not all(math.isfinite(value) and 0 <= value <= 60 for value in (pause, initial)):
            raise ValueError()
    except ValueError as error:
        raise DemoUnavailable("A configuração de ritmo da demonstração é inválida no servidor.") from error
    return {"dataset_root": root, "api_url": api_url, "metrics_endpoint": endpoint,
            "chunk_timestamps": chunk, "pause_seconds": pause, "initial_pause_seconds": initial}


class DemoService:
    def __init__(self, store: DemoStore | None = None):
        self.store = store or DemoStore()

    def recover_interrupted(self) -> None:
        guard = acquire_guard()
        if guard is not None:
            try:
                self.store.reconcile()
            finally:
                guard.close()

    def start(self, key: str | None = None) -> dict[str, Any]:
        key = key or str(uuid.uuid4())
        existing = self.store.by_key(key)
        if existing:
            return existing
        config = _configuration()
        guard = acquire_guard()
        if guard is None:
            # Same-key retries and different-key competing clicks have distinct outcomes.
            for attempt in range(6):
                existing = self.store.by_key(key)
                if existing:
                    return existing
                active = self.store.list(active_only=True)
                if active:
                    raise DemoBusy(active[0])
                if attempt < 5:
                    time.sleep(0.05)
            raise DemoBusy(None)
        created = None
        try:
            self.store.reconcile()
            existing = self.store.by_key(key)
            if existing:
                guard.close()
                return existing
            created = self.store.create(key)
            worker = threading.Thread(target=self._execute, args=(created["demo_run_id"], config, guard),
                                      name=f"aim-demo-{created['demo_run_id'][:8]}", daemon=True)
            worker.start()
            return created
        except Exception:
            if created is not None:
                try:
                    self.store.update(created["demo_run_id"], status="failed", progress={"current_stage": "failed"},
                                      error_code="worker_start_failed", message="Não foi possível iniciar a demonstração. Tente uma nova execução.")
                except Exception as persistence_error:
                    logger.error("Could not save worker-start failure (%s)", type(persistence_error).__name__)
            guard.close()
            raise

    def _execute(self, demo_id: str, config: dict[str, Any], guard: Any) -> None:
        try:
            self.store.update(demo_id, progress={"current_stage": "loading_source"})
            result = run_progressive(**config, include_ground_truth=True,
                on_progress=lambda progress: self.store.update(demo_id, progress=progress))
            self.store.update(demo_id, status="completed", progress={"current_stage": "completed",
                "replay_run_id": result["replay_run_id"], "completed_chunks": result["chunk_count"],
                "raw_point_count": result["source_point_count"],
                "latest_transform_run_id": result["final_transform"]["transform_run_id"],
                "latest_transform_60s_run_id": result["final_transform_60s"]["transform_run_id"]})
        except Exception as error:
            logger.error("Demonstration %s failed (%s)", demo_id, type(error).__name__)
            code, message = "demo_execution_failed", "A demonstração falhou. Os dados já persistidos foram preservados."
            if isinstance(error, (httpx.HTTPError, TimeoutError)):
                code, message = "transport_failed", "O envio OTLP ou a confirmação PostgreSQL falhou. Verifique API e Collector."
            elif isinstance(error, (FileNotFoundError, ValueError)):
                code, message = "source_validation_failed", "A fonte local ou o resultado do recorte não passou na validação."
            try:
                self.store.update(demo_id, status="failed", progress={"current_stage": "failed"}, error_code=code, message=message)
            except Exception as persistence_error:
                logger.error("Could not save failure for demonstration %s (%s)", demo_id, type(persistence_error).__name__)
        finally:
            guard.close()
