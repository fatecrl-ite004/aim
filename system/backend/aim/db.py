"""PostgreSQL connection and SQL migration helpers."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .settings import database_url


MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def connect(dsn: str | None = None) -> psycopg.Connection:
    return psycopg.connect(dsn or database_url(), row_factory=dict_row)


@contextmanager
def connection(dsn: str | None = None) -> Iterator[psycopg.Connection]:
    with connect(dsn) as conn:
        yield conn


def apply_migrations(dsn: str | None = None) -> list[str]:
    """Apply unapplied SQL files in order, atomically per migration."""
    applied_now: list[str] = []
    with connection(dsn) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS aim_schema_migration (
                   version TEXT PRIMARY KEY,
                   applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
               )"""
        )
        for path in sorted(MIGRATIONS_DIR.glob("[0-9]*.sql")):
            version = path.name
            if conn.execute("SELECT 1 FROM aim_schema_migration WHERE version = %s", (version,)).fetchone():
                continue
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO aim_schema_migration(version) VALUES (%s)", (version,))
            applied_now.append(version)
    return applied_now
