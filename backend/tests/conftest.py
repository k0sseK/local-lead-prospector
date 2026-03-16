"""
conftest.py – shared pytest fixtures for the backend test suite.

Strategy
--------
* Override DATABASE_URL to SQLite in-memory *before* any app module is
  imported so SQLAlchemy never tries to reach PostgreSQL.
* Each test receives a brand-new engine + schema so that db.commit() calls
  inside production code (e.g. increment_usage) don't leak state between tests.
* User fixture helpers are plain functions rather than fixtures that chain on
  `db`, which keeps the dependency graph simple.
"""

import os

# ── Env overrides MUST happen before any app import ──────────────────────────
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = ""  # force in-memory rate limiter for tests
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
# Disable cost-alert emails during tests (quota_service returns early when unset)
os.environ.pop("ADMIN_EMAIL", None)
os.environ.pop("RESEND_API_KEY", None)

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models  # noqa: F401 – registers all ORM classes with Base metadata


# ── Core DB fixture ───────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    """
    Provides a fresh in-memory SQLite session per test.

    A new engine (and therefore a new in-memory database) is created for every
    test function. This guarantees full isolation even when production code
    calls db.commit(), which would break a rollback-based isolation strategy.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ── User factory helper ───────────────────────────────────────────────────────

def _make_user(
    db,
    *,
    email: str,
    role: str = "user",
    plan: str = "free",
    monthly_credits: int = 0,
    credits_balance: int = 0,
) -> models.User:
    from app.quota_service import PLAN_MONTHLY_ALLOC, _first_of_next_month
    alloc = monthly_credits or PLAN_MONTHLY_ALLOC.get(plan, 15)
    user = models.User(
        email=email,
        hashed_password="$2b$12$fakehashforthisunittest0000000000000000000000",
        role=role,
        plan=plan,
        is_verified=True,
        monthly_credits=alloc,
        credits_balance=credits_balance,
        credits_reset_at=_first_of_next_month(),
    )
    db.add(user)
    db.flush()  # get auto-assigned id without committing
    return user


# ── User fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def free_user(db):
    return _make_user(db, email="free@test.local", role="user", plan="free")


@pytest.fixture()
def pro_user(db):
    return _make_user(db, email="pro@test.local", role="user", plan="pro")


@pytest.fixture()
def admin_user(db):
    # Admin quota bypass is based on role, not plan.
    return _make_user(db, email="admin@test.local", role="admin", plan="free")
