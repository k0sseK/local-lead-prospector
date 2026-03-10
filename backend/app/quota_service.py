"""
quota_service.py

Zarządza limitami zużycia per użytkownik (plan free/pro/admin).
Każdy audyt AI, skan Google Maps i wysyłka e-mail jest zliczana
w tabeli monthly_usage. Limity są resetowane automatycznie każdego
miesiąca (nowy rekord per miesiąc).
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from . import models

logger = logging.getLogger(__name__)

# Limity miesięczne per plan
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "ai_audits": 10,
        "scans": 5,
        "emails_sent": 20,
    },
    "pro": {
        "ai_audits": 300,
        "scans": 50,
        "emails_sent": 500,
    },
    "admin": {
        "ai_audits": 999_999,
        "scans": 999_999,
        "emails_sent": 999_999,
    },
}

# Szacunkowy koszt per akcja (USD) — Gemini 2.5 Flash
ACTION_COST_USD: dict[str, float] = {
    "ai_audits": 0.000218,
    "scans": 0.0,       # koszt Google Places po stronie serwera (nie śledzimy tu)
    "emails_sent": 0.0,
}


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_or_create_usage(db: Session, user_id: int) -> models.MonthlyUsage:
    month = _current_month()
    usage = (
        db.query(models.MonthlyUsage)
        .filter_by(user_id=user_id, month=month)
        .first()
    )
    if not usage:
        usage = models.MonthlyUsage(user_id=user_id, month=month)
        db.add(usage)
        db.flush()
    return usage


def check_quota(db: Session, user: models.User, action: str) -> bool:
    """Zwraca True jeśli użytkownik może wykonać akcję (w ramach limitu)."""
    plan = user.plan or "free"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    limit = limits.get(action, 0)

    month = _current_month()
    usage = (
        db.query(models.MonthlyUsage)
        .filter_by(user_id=user.id, month=month)
        .first()
    )
    if not usage:
        return True  # brak rekordu = user nie zużył nic w tym miesiącu

    current = getattr(usage, action, 0) or 0
    return current < limit


def get_quota_info(db: Session, user: models.User) -> dict:
    """Zwraca bieżące zużycie i limity użytkownika."""
    plan = user.plan or "free"
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    month = _current_month()
    usage = (
        db.query(models.MonthlyUsage)
        .filter_by(user_id=user.id, month=month)
        .first()
    )
    return {
        "plan": plan,
        "month": month,
        "usage": {
            "ai_audits": getattr(usage, "ai_audits", 0) or 0,
            "scans": getattr(usage, "scans", 0) or 0,
            "emails_sent": getattr(usage, "emails_sent", 0) or 0,
        },
        "limits": limits,
    }


def increment_usage(
    db: Session,
    user: models.User,
    action: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    lead_id: int = None,
):
    """Inkrementuje miesięczny licznik i loguje zdarzenie."""
    usage = _get_or_create_usage(db, user.id)
    current = getattr(usage, action, 0) or 0
    setattr(usage, action, current + 1)

    cost = ACTION_COST_USD.get(action, 0.0)
    if tokens_in:
        usage.tokens_in = (usage.tokens_in or 0) + tokens_in
    if tokens_out:
        usage.tokens_out = (usage.tokens_out or 0) + tokens_out
    if cost:
        usage.cost_usd = float(usage.cost_usd or 0) + cost

    event = models.UsageEvent(
        user_id=user.id,
        event_type=action,
        lead_id=lead_id,
        tokens_in=tokens_in or None,
        tokens_out=tokens_out or None,
        cost_usd=cost or None,
    )
    db.add(event)
    db.commit()
    logger.info("Usage incremented: user=%d action=%s month=%s", user.id, action, _current_month())
