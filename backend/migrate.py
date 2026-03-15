#!/usr/bin/env python3
"""
Brownfield-safe Alembic migration runner.

Logic:
  1. If `alembic_version` table does NOT exist but `users` table DOES exist →
     existing production DB managed previously by create_all() + ALTER TABLE.
     Stamp at `head` so Alembic knows schema is already up-to-date, then
     run upgrade head (no-op).
  2. Otherwise → run `alembic upgrade head` normally (fresh DB or already
     managed by Alembic).

Run from the backend/ directory (where alembic.ini lives):
    python migrate.py
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("migrate")

# Ensure app package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic import command

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://llp_user:llp_password@localhost:5432/llp_db",
)

# Railway injects postgres:// URIs; SQLAlchemy 1.4+ requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))


def main() -> None:
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    has_alembic_version = inspector.has_table("alembic_version")
    has_users = inspector.has_table("users")

    if not has_alembic_version and has_users:
        log.info(
            "Brownfield DB detected: schema exists without Alembic version table. "
            "Stamping at head revision to skip initial migration DDL..."
        )
        command.stamp(alembic_cfg, "head")
        log.info("Stamp complete.")
    else:
        log.info("Running alembic upgrade head...")

    command.upgrade(alembic_cfg, "head")
    log.info("Migrations complete.")


if __name__ == "__main__":
    main()
