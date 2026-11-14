"""Controlled asynchronous demonstration endpoints; request data never becomes a command."""

from __future__ import annotations

import psycopg
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from uuid import UUID

from .demo_runs import DemoBusy, DemoService, DemoStore, DemoUnavailable
from .repository import NotFound

router = APIRouter(prefix="/api/v1/demo-runs", tags=["demonstrations"])


class StartDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _database_error(error: psycopg.Error) -> HTTPException:
    return HTTPException(503, detail={"code": "database_unavailable", "message": "A demonstração precisa do PostgreSQL e das migrations atualizadas."})


@router.post("", status_code=202)
def start_demo(payload: StartDemoRequest, idempotency_key: UUID | None = Header(default=None)) -> dict:
    try:
        return DemoService().start(str(idempotency_key) if idempotency_key else None)
    except DemoBusy as error:
        active = error.active or {}
        raise HTTPException(409, detail={"code": "demo_already_running", "message": "Já existe uma demonstração em execução.",
            "demo_run_id": active.get("demo_run_id"), "replay_run_id": active.get("replay_run_id")}) from error
    except DemoUnavailable as error:
        raise HTTPException(503, detail={"code": "demo_unavailable", "message": str(error)}) from error
    except psycopg.Error as error:
        raise _database_error(error) from error


@router.get("/active")
def active_demo() -> dict:
    try:
        DemoService().recover_interrupted()
        active = DemoStore().list(active_only=True)
        return {"demo_run": active[0] if active else None}
    except psycopg.Error as error:
        raise _database_error(error) from error


@router.get("")
def list_demos() -> dict:
    try:
        return {"demo_runs": DemoStore().list()}
    except psycopg.Error as error:
        raise _database_error(error) from error


@router.get("/{demo_run_id}")
def get_demo(demo_run_id: UUID) -> dict:
    try:
        return DemoStore().get(str(demo_run_id))
    except NotFound as error:
        raise HTTPException(404, detail="Demonstração não encontrada.") from error
    except psycopg.Error as error:
        raise _database_error(error) from error
