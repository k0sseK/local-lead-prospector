"""
test_quota_service.py – unit tests for app/quota_service.py (credit-based system)

What is tested
--------------
check_credits
  - fresh free user has 15 monthly credits → allowed
  - user with enough credits → allowed
  - user with 0 credits → denied
  - admin role: bypasses credits entirely
  - unverified free user → denied

spend_credits
  - spends from monthly_credits first
  - overflow to credits_balance when monthly exhausted
  - admin does not lose credits

get_credits_info
  - free user receives correct plan info
  - pro user receives correct plan info
  - admin gets unlimited credits

increment_usage (tracking)
  - counter increments by exactly 1 per call
  - tokens tracked for ai_audits
  - UsageEvent row created with correct fields
"""

import pytest
from unittest.mock import patch

from app import models
from app.quota_service import (
    PLAN_MONTHLY_ALLOC,
    ACTION_COSTS,
    SCAN_COST,
    AUDIT_COST,
    SEQUENCE_COST,
    check_credits,
    spend_credits,
    get_credits_info,
    increment_usage,
)

_MONTH = "2026-03"


def _seed_usage(db, user, *, month=_MONTH, **counters) -> models.MonthlyUsage:
    """Insert a MonthlyUsage row with the given counter values."""
    usage = models.MonthlyUsage(user_id=user.id, month=month, **counters)
    db.add(usage)
    db.flush()
    return usage


# ─── check_credits ───────────────────────────────────────────────────────────

class TestCheckCredits:

    def test_fresh_free_user_has_credits_and_is_allowed(self, db, free_user):
        """Free user starts with 15 monthly credits → can do any action."""
        assert check_credits(db, free_user, "ai_audits") is True
        assert check_credits(db, free_user, "scans") is True
        assert check_credits(db, free_user, "emails_sent") is True

    def test_user_with_zero_credits_is_denied(self, db, free_user):
        free_user.monthly_credits = 0
        free_user.credits_balance = 0
        db.commit()
        assert check_credits(db, free_user, "scans") is False  # costs 3
        assert check_credits(db, free_user, "ai_audits") is False  # costs 2

    def test_user_with_exact_credits_for_action_is_allowed(self, db, free_user):
        free_user.monthly_credits = SCAN_COST  # exactly 3
        free_user.credits_balance = 0
        db.commit()
        assert check_credits(db, free_user, "scans") is True

    def test_user_with_less_than_action_cost_is_denied(self, db, free_user):
        free_user.monthly_credits = SCAN_COST - 1  # 2, need 3
        free_user.credits_balance = 0
        db.commit()
        assert check_credits(db, free_user, "scans") is False

    def test_credits_balance_supplements_monthly(self, db, free_user):
        """credits_balance (from packs) adds to monthly for total check."""
        free_user.monthly_credits = 1
        free_user.credits_balance = 5
        db.commit()
        assert check_credits(db, free_user, "scans") is True  # 1+5=6 >= 3

    def test_unverified_free_user_is_denied(self, db, free_user):
        free_user.is_verified = False
        db.commit()
        assert check_credits(db, free_user, "ai_audits") is False
        assert check_credits(db, free_user, "scans") is False

    def test_admin_bypasses_credits_entirely(self, db, admin_user):
        admin_user.monthly_credits = 0
        admin_user.credits_balance = 0
        db.commit()
        assert check_credits(db, admin_user, "ai_audits") is True
        assert check_credits(db, admin_user, "scans") is True

    def test_pro_user_has_more_monthly_credits_than_free(self, db, pro_user, free_user):
        assert pro_user.monthly_credits > free_user.monthly_credits


# ─── spend_credits ───────────────────────────────────────────────────────────

class TestSpendCredits:

    def test_spends_from_monthly_first(self, db, free_user):
        free_user.monthly_credits = 10
        free_user.credits_balance = 20
        db.commit()

        spend_credits(db, free_user, "scans")  # costs 3

        assert free_user.monthly_credits == 7
        assert free_user.credits_balance == 20  # untouched

    def test_overflows_to_balance_when_monthly_exhausted(self, db, free_user):
        free_user.monthly_credits = 1
        free_user.credits_balance = 10
        db.commit()

        spend_credits(db, free_user, "scans")  # costs 3, monthly has 1

        assert free_user.monthly_credits == 0
        assert free_user.credits_balance == 8  # 10 - (3-1) = 8

    def test_admin_does_not_lose_credits(self, db, admin_user):
        admin_user.monthly_credits = 5
        admin_user.credits_balance = 10
        db.commit()

        spend_credits(db, admin_user, "scans")

        assert admin_user.monthly_credits == 5
        assert admin_user.credits_balance == 10

    def test_multiple_spends_accumulate(self, db, pro_user):
        initial = pro_user.monthly_credits

        spend_credits(db, pro_user, "ai_audits")  # -2
        spend_credits(db, pro_user, "ai_audits")  # -2
        spend_credits(db, pro_user, "scans")       # -3

        assert pro_user.monthly_credits == initial - 2 - 2 - 3

    def test_action_costs_are_correct(self):
        assert SCAN_COST == 3
        assert AUDIT_COST == 2
        assert SEQUENCE_COST == 1


# ─── get_credits_info ────────────────────────────────────────────────────────

class TestGetCreditsInfo:

    def test_free_user_info(self, db, free_user):
        info = get_credits_info(db, free_user)
        assert info["plan"] == "free"
        assert info["monthly_credits_limit"] == PLAN_MONTHLY_ALLOC["free"]
        assert info["action_costs"]["scan"] == SCAN_COST
        assert info["action_costs"]["ai_audit"] == AUDIT_COST
        assert info["is_verified"] is True

    def test_pro_user_info(self, db, pro_user):
        info = get_credits_info(db, pro_user)
        assert info["plan"] == "pro"
        assert info["monthly_credits_limit"] == PLAN_MONTHLY_ALLOC["pro"]

    def test_admin_gets_unlimited(self, db, admin_user):
        info = get_credits_info(db, admin_user)
        assert info["plan"] == "admin"
        assert info["monthly_credits"] == 999999

    def test_total_credits_sums_monthly_and_balance(self, db, free_user):
        free_user.credits_balance = 50
        db.commit()
        info = get_credits_info(db, free_user)
        assert info["total_credits"] == free_user.monthly_credits + 50

    def test_unverified_user_shows_as_unverified(self, db, free_user):
        free_user.is_verified = False
        db.commit()
        info = get_credits_info(db, free_user)
        assert info["is_verified"] is False


# ─── increment_usage (tracking) ─────────────────────────────────────────────

class TestIncrementUsage:

    def test_creates_monthly_usage_record(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage is not None
        assert usage.scans == 1

    def test_increments_existing_record(self, db, free_user):
        _seed_usage(db, free_user, month=_MONTH, scans=3)

        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage.scans == 4

    def test_ai_audit_tracks_tokens(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "ai_audits", tokens_in=900, tokens_out=500)

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage.tokens_in == 900
        assert usage.tokens_out == 500

    def test_creates_usage_event(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "ai_audits", tokens_in=100, tokens_out=50, lead_id=42)

        event = (
            db.query(models.UsageEvent)
            .filter_by(user_id=free_user.id)
            .first()
        )
        assert event is not None
        assert event.event_type == "ai_audits"
        assert event.lead_id == 42
        assert event.tokens_in == 100

    def test_scan_has_null_cost_in_event(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")

        event = (
            db.query(models.UsageEvent)
            .filter_by(user_id=free_user.id)
            .first()
        )
        assert event.cost_usd is None
