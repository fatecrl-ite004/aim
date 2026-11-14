"""Runtime settings for the local V1 backend."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPOSITORY_ROOT / ".env.v1", override=False)


def database_url() -> str:
    value = os.getenv("AIM_DATABASE_URL")
    if not value:
        raise RuntimeError("AIM_DATABASE_URL is required; see .env.v1 or set it in the process environment")
    return value


def otlp_max_body_bytes() -> int:
    raw = os.getenv("AIM_OTLP_MAX_BODY_BYTES", str(64 * 1024 * 1024))
    try:
        value = int(raw)
    except ValueError as exc:
        raise RuntimeError("AIM_OTLP_MAX_BODY_BYTES must be an integer") from exc
    if value < 1024:
        raise RuntimeError("AIM_OTLP_MAX_BODY_BYTES must be at least 1024")
    return value
