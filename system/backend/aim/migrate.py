"""Run the local PostgreSQL migrations once or refresh an existing schema."""

from __future__ import annotations

from .db import apply_migrations


def main() -> int:
    applied = apply_migrations()
    if applied:
        for version in applied:
            print(f"applied {version}")
    else:
        print("database schema is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
