"""FastAPI entrypoint for the local historical-replay API."""

from __future__ import annotations

import hashlib
import logging
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .otlp import OTLP_PROTOBUF_MEDIA_TYPE, OtlpProfileError, decode_metrics_request, status_payload, success_payload
from .read_api import router as read_router
from .repository import Conflict, InvalidData, NotFound, Repository
from .settings import otlp_max_body_bytes
from .demo_api import router as demo_router
from .demo_runs import DemoService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aim.backend")

@asynccontextmanager
async def lifespan(application: FastAPI):
    try:
        DemoService().recover_interrupted()
    except psycopg.Error as error:
        logger.warning("Demonstration recovery unavailable (%s); apply migrations", type(error).__name__)
    yield


app = FastAPI(title="AIM V1 Replay API", version="1.0.0", lifespan=lifespan)
app.include_router(read_router)
app.include_router(demo_router)


def _otlp_error(status_code: int, grpc_code: int, message: str) -> Response:
    return Response(
        content=status_payload(grpc_code, message),
        status_code=status_code,
        media_type=OTLP_PROTOBUF_MEDIA_TYPE,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/health/live")
def live() -> JSONResponse:
    return JSONResponse(content={"status": "live"})


@app.get("/health/ready")
def ready() -> JSONResponse:
    try:
        if not Repository().check_ready():
            return JSONResponse(status_code=503, content={"status": "not_ready", "dependency": "postgresql_schema"})
    except Exception as error:
        logger.warning("Readiness check failed (%s)", type(error).__name__)
        return JSONResponse(status_code=503, content={"status": "not_ready", "dependency": "postgresql"})
    return JSONResponse(content={"status": "ready", "dependency": "postgresql"})


@app.post("/v1/metrics", include_in_schema=True)
async def receive_metrics(request: Request) -> Response:
    """Accept one full OTLP request atomically and acknowledge only after commit."""
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != OTLP_PROTOBUF_MEDIA_TYPE:
        return _otlp_error(415, 3, "This receiver accepts OTLP/HTTP binary Protobuf only")
    content_encoding = request.headers.get("content-encoding", "identity").strip().lower()
    if content_encoding not in ("", "identity"):
        return _otlp_error(415, 3, "Compressed OTLP requests are outside the V1 receiver profile")
    payload = await request.body()
    if len(payload) > otlp_max_body_bytes():
        return _otlp_error(413, 8, "OTLP request exceeds the configured body size limit")
    try:
        replay_id, points = decode_metrics_request(payload)
        batch = await run_in_threadpool(Repository().record_batch_and_raw_points,
            replay_id, hashlib.sha256(payload).hexdigest(), points
        )
    except OtlpProfileError as error:
        return _otlp_error(error.http_status, error.grpc_code, error.message)
    except NotFound as error:
        return _otlp_error(404, 5, str(error))
    except Conflict as error:
        return _otlp_error(409, 6, str(error))
    except InvalidData as error:
        return _otlp_error(400, 3, str(error))
    except psycopg.Error as error:
        logger.error("OTLP PostgreSQL write failed (%s)", type(error).__name__)
        return _otlp_error(503, 14, "PostgreSQL write failed; the OTLP request was not acknowledged")
    except Exception as error:
        logger.exception("Unexpected OTLP receiver failure (%s)", type(error).__name__)
        return _otlp_error(500, 13, "OTLP receiver failed before acknowledging the request")

    logger.info(
        "OTLP batch committed replay=%s batch=%s accepted=%s inserted=%s",
        replay_id,
        batch["ingest_batch_id"],
        batch["accepted_data_points"],
        batch["inserted_data_points"],
    )
    return Response(
        content=success_payload(),
        status_code=200,
        media_type=OTLP_PROTOBUF_MEDIA_TYPE,
        headers={"Cache-Control": "no-store"},
    )
