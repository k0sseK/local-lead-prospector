"""
quota_service.py

Zarządza limitami zużycia per użytkownik (plan free/pro).
Admini (role='admin') mają zawsze nieograniczone limity, niezależnie od planu.
Każdy audyt AI, skan Google Maps i wysyłka e-mail jest zliczana
w tabeli monthly_usage. Limity są resetowane automatycznie każdego
miesiąca (nowy rekord per miesiąc).
"""
import logging
import os
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models

logger = logging.getLogger(__name__)

# Limity miesięczne per plan (role='admin' → zawsze nieograniczone, patrz check_quota/get_quota_info)
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
}

_UNLIMITED: dict[str, int] = {
    "ai_audits": 999_999,
    "scans": 999_999,
    "emails_sent": 999_999,
}

_UNVERIFIED_FREE_LIMITS: dict[str, int] = {
    "ai_audits": 0,
    "scans": 0,
    "emails_sent": 0,
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
    if user.role == "admin":
        return True  # admini mają zawsze nieograniczone limity
    plan = user.plan or "free"
    
    if plan == "free" and not getattr(user, "is_verified", False):
        return False
        
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
    if user.role == "admin":
        limits = _UNLIMITED
        plan = "admin"  # wyświetlamy 'admin' w UI dla roli admin
    elif plan == "free" and not getattr(user, "is_verified", False):
        limits = _UNVERIFIED_FREE_LIMITS
    else:
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
        "is_verified": bool(getattr(user, "is_verified", False)),
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

    # Trigger cost alert check after AI audits (only action with non-zero cost)
    if action == "ai_audits":
        _check_daily_cost_alert(db)


# ─── Daily cost alert ─────────────────────────────────────────────────────────
_cost_alert_sent_date: str | None = None  # in-process deduplication flag


def _check_daily_cost_alert(db: Session) -> None:
    """Sends one alert email per day if total AI cost exceeds threshold."""
    global _cost_alert_sent_date

    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return  # no alert destination configured

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _cost_alert_sent_date == today_str:
        return  # already alerted today

    threshold = float(os.getenv("ADMIN_COST_ALERT_USD", "2.0"))

    # Sum all AI audit costs for today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total = db.query(func.sum(models.UsageEvent.cost_usd)).filter(
        models.UsageEvent.event_type == "ai_audits",
        models.UsageEvent.created_at >= today_start,
    ).scalar() or 0.0

    if float(total) < threshold:
        return

    logger.warning(
        "COST ALERT: daily AI cost $%.4f exceeded threshold $%.2f — sending alert to %s",
        float(total), threshold, admin_email,
    )
    _cost_alert_sent_date = today_str  # mark before sending to avoid duplicates on error

    try:
        import resend as resend_lib
        resend_lib.api_key = os.getenv("RESEND_API_KEY", "")
        from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        if not resend_lib.api_key:
            return
        resend_lib.Emails.send({
            "from": from_email,
            "to": [admin_email],
            "subject": f"[znajdzfirmy.pl] Alert kosztowy: ${float(total):.2f} dzisiaj",
            "html": (
                f"<p>Dzienny koszt AI przekroczył próg <strong>${threshold:.2f}</strong>.</p>"
                f"<p>Łączny koszt dzisiaj: <strong>${float(total):.4f}</strong></p>"
                f"<p>Rozważ tymczasowe podwyższenie limitu lub sprawdzenie zużycia w panelu admina.</p>"
            ),
        })
        logger.info("Cost alert email sent to %s", admin_email)
    except Exception as exc:
        logger.error("Failed to send cost alert email: %s", exc)
