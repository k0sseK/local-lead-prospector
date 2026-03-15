"""
quota_service.py

Zarządza kredytami użytkowników (system kredytowy zastępuje stare limity miesięczne).

Każdy użytkownik ma dwie pule kredytów:
  - monthly_credits  — z planu, resetowane co miesiąc (z rolloverem dla pro/pro_annual)
  - credits_balance  — z jednorazowych paczek, nigdy nie wygasają

Koszty akcji:
  - Skan Google Maps:  3 kredyty
  - Audyt AI:          2 kredyty
  - Sekwencja email:   1 kredyt

Plany:
  - free:        15 kr/mies, brak rollover
  - pro:         250 kr/mies, rollover maks 500
  - pro_annual:  250 kr/mies, rollover maks 500

Admini (role='admin') mają zawsze nieograniczony dostęp.
"""
import logging
import os
from datetime import datetime, timezone
from calendar import monthrange
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models

logger = logging.getLogger(__name__)

# ─── Koszty akcji (kredyty) ────────────────────────────────────────────────────
SCAN_COST     = 3
AUDIT_COST    = 2
SEQUENCE_COST = 1

ACTION_COSTS: dict[str, int] = {
    "scans":       SCAN_COST,
    "ai_audits":   AUDIT_COST,
    "emails_sent": SEQUENCE_COST,
}

# ─── Konfiguracja planów ───────────────────────────────────────────────────────
PLAN_MONTHLY_ALLOC: dict[str, int] = {
    "free":       15,
    "pro":        250,
    "pro_annual": 250,
}

PLAN_ROLLOVER_CAP: dict[str, int] = {
    "free":       15,   # brak rollover — po prostu nie przekroczy przydziału
    "pro":        500,
    "pro_annual": 500,
}

# Szacunkowy koszt per akcja (USD) — Gemini 2.5 Flash (do śledzenia kosztów admin)
ACTION_COST_USD: dict[str, float] = {
    "ai_audits":   0.000218,
    "scans":       0.0,
    "emails_sent": 0.0,
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _first_of_next_month() -> datetime:
    """Zwraca datetime 1. dnia następnego miesiąca o 00:00 UTC."""
    now = datetime.now(timezone.utc)
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, 0, 0, 0)
    return datetime(now.year, now.month + 1, 1, 0, 0, 0)


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


# ─── Credit logic ─────────────────────────────────────────────────────────────

def reset_monthly_credits_if_due(db: Session, user: models.User) -> None:
    """Resetuje monthly_credits jeśli credits_reset_at minął lub nie jest ustawiony."""
    now = datetime.now(timezone.utc)
    if user.credits_reset_at is not None:
        reset_at = user.credits_reset_at
        # Ensure timezone-aware comparison
        if reset_at.tzinfo is None:
            reset_at = reset_at.replace(tzinfo=timezone.utc)
        if now < reset_at:
            return  # reset jeszcze nie należy

    plan = user.plan or "free"
    alloc = PLAN_MONTHLY_ALLOC.get(plan, 15)
    cap   = PLAN_ROLLOVER_CAP.get(plan, 15)

    if plan == "free":
        # brak rollover — zastępujemy przydziałem
        user.monthly_credits = alloc
    else:
        # rollover: dodajemy nowy przydział do pozostałych, ale max cap
        user.monthly_credits = min((user.monthly_credits or 0) + alloc, cap)

    user.credits_reset_at = _first_of_next_month()
    db.commit()
    logger.info(
        "Monthly credits reset for user=%d plan=%s → monthly_credits=%d next_reset=%s",
        user.id, plan, user.monthly_credits, user.credits_reset_at,
    )


def check_credits(db: Session, user: models.User, action: str) -> bool:
    """Zwraca True jeśli użytkownik ma wystarczająco kredytów na wykonanie akcji."""
    if user.role == "admin":
        return True

    # Niezweryfikowani użytkownicy free nie mogą nic robić
    if (user.plan or "free") == "free" and not getattr(user, "is_verified", False):
        return False

    reset_monthly_credits_if_due(db, user)

    cost = ACTION_COSTS.get(action, 0)
    total = (user.monthly_credits or 0) + (user.credits_balance or 0)
    return total >= cost


def spend_credits(db: Session, user: models.User, action: str) -> None:
    """Odejmuje kredyty za akcję. Najpierw z monthly_credits, potem z credits_balance."""
    if user.role == "admin":
        return  # admini nie zużywają kredytów

    cost = ACTION_COSTS.get(action, 0)
    if cost <= 0:
        return

    monthly = user.monthly_credits or 0
    if monthly >= cost:
        user.monthly_credits = monthly - cost
    else:
        remainder = cost - monthly
        user.monthly_credits = 0
        user.credits_balance = max(0, (user.credits_balance or 0) - remainder)

    db.commit()
    logger.info(
        "Credits spent: user=%d action=%s cost=%d → monthly=%d balance=%d",
        user.id, action, cost, user.monthly_credits, user.credits_balance,
    )


def get_credits_info(db: Session, user: models.User) -> dict:
    """Zwraca stan kredytów użytkownika (używane przez GET /api/usage)."""
    if user.role == "admin":
        return {
            "plan": "admin",
            "monthly_credits": 999999,
            "monthly_credits_limit": 999999,
            "credits_balance": 0,
            "total_credits": 999999,
            "credits_reset_at": None,
            "is_verified": True,
            "action_costs": {
                "scan": SCAN_COST,
                "ai_audit": AUDIT_COST,
                "email_sequence": SEQUENCE_COST,
            },
        }

    plan = user.plan or "free"
    reset_monthly_credits_if_due(db, user)

    monthly     = user.monthly_credits or 0
    balance     = user.credits_balance or 0
    alloc       = PLAN_MONTHLY_ALLOC.get(plan, 15)
    reset_at    = user.credits_reset_at

    return {
        "plan": plan,
        "monthly_credits": monthly,
        "monthly_credits_limit": alloc,
        "credits_balance": balance,
        "total_credits": monthly + balance,
        "credits_reset_at": reset_at.isoformat() if reset_at else None,
        "is_verified": bool(getattr(user, "is_verified", False)),
        "action_costs": {
            "scan": SCAN_COST,
            "ai_audit": AUDIT_COST,
            "email_sequence": SEQUENCE_COST,
        },
    }


# ─── increment_usage — zachowane do śledzenia kosztów AI (admin stats) ────────

def increment_usage(
    db: Session,
    user: models.User,
    action: str,
    tokens_in: int = 0,
    tokens_out: int = 0,
    lead_id: int = None,
):
    """Loguje zdarzenie do MonthlyUsage + UsageEvent (śledzenie kosztów tokenów AI)."""
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
    logger.info("Usage logged: user=%d action=%s month=%s", user.id, action, _current_month())

    if action == "ai_audits":
        _check_daily_cost_alert(db)


# ─── Daily cost alert ─────────────────────────────────────────────────────────
_cost_alert_sent_date: str | None = None


def _check_daily_cost_alert(db: Session) -> None:
    """Sends one alert email per day if total AI cost exceeds threshold."""
    global _cost_alert_sent_date

    admin_email = os.getenv("ADMIN_EMAIL")
    if not admin_email:
        return

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _cost_alert_sent_date == today_str:
        return

    threshold = float(os.getenv("ADMIN_COST_ALERT_USD", "2.0"))

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
    _cost_alert_sent_date = today_str

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
