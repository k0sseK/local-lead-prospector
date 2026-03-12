"""
test_quota_service.py – unit tests for app/quota_service.py

What is tested
--------------
check_quota
  - fresh user (no MonthlyUsage record) → always allowed
  - free plan: allowed when under limit, denied when at limit
  - pro plan: allowed when under higher limit, denied when at limit
  - admin role: bypasses quota entirely, even with absurd counters
  - monthly isolation: exhausted previous month does NOT block the new month

increment_usage
  - counter increments by exactly 1 per call
  - multiple calls accumulate
  - tokens_in / tokens_out / cost_usd tracked for ai_audits
  - UsageEvent row is created with correct fields
  - scan action writes NULL cost (no monetary cost)

get_quota_info
  - free user receives free-plan limits
  - pro user receives pro-plan limits
  - admin user receives unlimited limits and plan="admin"
  - live usage counters are reflected accurately
  - fresh user shows all-zero usage
"""

import pytest
from unittest.mock import patch

from app import models
from app.quota_service import (
    PLAN_LIMITS,
    _UNLIMITED,
    check_quota,
    get_quota_info,
    increment_usage,
)

_MONTH = "2026-03"
_PREV_MONTH = "2026-02"
_NEXT_MONTH = "2026-04"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _seed_usage(db, user, *, month=_MONTH, **counters) -> models.MonthlyUsage:
    """Insert a MonthlyUsage row with the given counter values."""
    usage = models.MonthlyUsage(user_id=user.id, month=month, **counters)
    db.add(usage)
    db.flush()
    return usage


# ─── check_quota ──────────────────────────────────────────────────────────────

class TestCheckQuota:

    def test_fresh_user_no_record_always_allowed(self, db, free_user):
        """No MonthlyUsage record → user hasn't used anything → all actions allowed."""
        assert check_quota(db, free_user, "ai_audits") is True
        assert check_quota(db, free_user, "scans") is True
        assert check_quota(db, free_user, "emails_sent") is True

    # ── free plan ─────────────────────────────────────────────────────────────

    def test_free_user_under_limit_is_allowed(self, db, free_user):
        _seed_usage(db, free_user, month=_MONTH, ai_audits=9, scans=4, emails_sent=19)
        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, free_user, "ai_audits") is True
            assert check_quota(db, free_user, "scans") is True
            assert check_quota(db, free_user, "emails_sent") is True

    def test_free_user_exactly_at_limit_is_denied(self, db, free_user):
        """Used == limit means the *next* action would exceed it → deny."""
        _seed_usage(
            db, free_user, month=_MONTH,
            ai_audits=PLAN_LIMITS["free"]["ai_audits"],
            scans=PLAN_LIMITS["free"]["scans"],
            emails_sent=PLAN_LIMITS["free"]["emails_sent"],
        )
        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, free_user, "ai_audits") is False
            assert check_quota(db, free_user, "scans") is False
            assert check_quota(db, free_user, "emails_sent") is False

    # ── pro plan ──────────────────────────────────────────────────────────────

    def test_pro_user_under_higher_limit_is_allowed(self, db, pro_user):
        # One below the pro limit – must still be allowed.
        _seed_usage(
            db, pro_user, month=_MONTH,
            ai_audits=PLAN_LIMITS["pro"]["ai_audits"] - 1,
            scans=PLAN_LIMITS["pro"]["scans"] - 1,
        )
        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, pro_user, "ai_audits") is True
            assert check_quota(db, pro_user, "scans") is True

    def test_pro_user_at_limit_is_denied(self, db, pro_user):
        _seed_usage(
            db, pro_user, month=_MONTH,
            ai_audits=PLAN_LIMITS["pro"]["ai_audits"],
        )
        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, pro_user, "ai_audits") is False

    def test_pro_limit_is_higher_than_free_limit(self, db):
        """Sanity: pro limits must exceed free limits for every action."""
        for action in ("ai_audits", "scans", "emails_sent"):
            assert PLAN_LIMITS["pro"][action] > PLAN_LIMITS["free"][action], (
                f"pro limit for '{action}' must be > free limit"
            )

    # ── admin role ────────────────────────────────────────────────────────────

    def test_admin_bypasses_quota_regardless_of_usage(self, db, admin_user):
        """Admin role must always return True, even with absurdly high counters."""
        _seed_usage(
            db, admin_user, month=_MONTH,
            ai_audits=999_999,
            scans=999_999,
            emails_sent=999_999,
        )
        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, admin_user, "ai_audits") is True
            assert check_quota(db, admin_user, "scans") is True
            assert check_quota(db, admin_user, "emails_sent") is True

    # ── monthly reset ─────────────────────────────────────────────────────────

    def test_exhausted_previous_month_does_not_block_new_month(self, db, free_user):
        """Usage keyed to an old month must be invisible in the current month."""
        _seed_usage(
            db, free_user, month=_PREV_MONTH,
            ai_audits=PLAN_LIMITS["free"]["ai_audits"],  # fully exhausted
        )
        with patch("app.quota_service._current_month", return_value=_NEXT_MONTH):
            assert check_quota(db, free_user, "ai_audits") is True

    def test_two_months_tracked_independently(self, db, free_user):
        """Records for two different months coexist without interfering."""
        _seed_usage(db, free_user, month=_PREV_MONTH, ai_audits=10)  # exhausted
        _seed_usage(db, free_user, month=_MONTH, ai_audits=5)         # not exhausted

        with patch("app.quota_service._current_month", return_value=_PREV_MONTH):
            assert check_quota(db, free_user, "ai_audits") is False

        with patch("app.quota_service._current_month", return_value=_MONTH):
            assert check_quota(db, free_user, "ai_audits") is True


# ─── increment_usage ──────────────────────────────────────────────────────────

class TestIncrementUsage:

    def test_creates_monthly_usage_record_on_first_call(self, db, free_user):
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

    def test_multiple_increments_accumulate(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")
            increment_usage(db, free_user, "scans")
            increment_usage(db, free_user, "scans")

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage.scans == 3

    def test_ai_audit_tracks_tokens_and_cost(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "ai_audits", tokens_in=900, tokens_out=500)

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage.tokens_in == 900
        assert usage.tokens_out == 500
        assert float(usage.cost_usd) > 0.0, "ai_audits should have a non-zero USD cost"

    def test_ai_audit_cost_accumulates_across_calls(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "ai_audits", tokens_in=900, tokens_out=500)
            increment_usage(db, free_user, "ai_audits", tokens_in=900, tokens_out=500)

        usage = (
            db.query(models.MonthlyUsage)
            .filter_by(user_id=free_user.id, month=_MONTH)
            .first()
        )
        assert usage.ai_audits == 2
        assert usage.tokens_in == 1800
        assert float(usage.cost_usd) > 0.0

    def test_creates_usage_event_record(self, db, free_user):
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
        assert event.tokens_out == 50

    def test_scan_has_null_cost_in_event(self, db, free_user):
        """Scans don't cost anything – cost_usd must be NULL, not 0."""
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")

        event = (
            db.query(models.UsageEvent)
            .filter_by(user_id=free_user.id)
            .first()
        )
        assert event.cost_usd is None

    def test_scan_has_null_tokens_in_event(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")

        event = (
            db.query(models.UsageEvent)
            .filter_by(user_id=free_user.id)
            .first()
        )
        assert event.tokens_in is None
        assert event.tokens_out is None

    def test_each_call_creates_one_event(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            increment_usage(db, free_user, "scans")
            increment_usage(db, free_user, "scans")

        events = (
            db.query(models.UsageEvent)
            .filter_by(user_id=free_user.id)
            .all()
        )
        assert len(events) == 2


# ─── get_quota_info ───────────────────────────────────────────────────────────

class TestGetQuotaInfo:

    def test_free_user_gets_free_plan_limits(self, db, free_user):
        info = get_quota_info(db, free_user)

        assert info["plan"] == "free"
        assert info["limits"]["ai_audits"] == PLAN_LIMITS["free"]["ai_audits"]
        assert info["limits"]["scans"] == PLAN_LIMITS["free"]["scans"]
        assert info["limits"]["emails_sent"] == PLAN_LIMITS["free"]["emails_sent"]

    def test_pro_user_gets_pro_plan_limits(self, db, pro_user):
        info = get_quota_info(db, pro_user)

        assert info["plan"] == "pro"
        assert info["limits"]["ai_audits"] == PLAN_LIMITS["pro"]["ai_audits"]
        assert info["limits"]["scans"] == PLAN_LIMITS["pro"]["scans"]

    def test_admin_gets_unlimited_limits_and_admin_plan_label(self, db, admin_user):
        info = get_quota_info(db, admin_user)

        assert info["plan"] == "admin"
        assert info["limits"]["ai_audits"] == _UNLIMITED["ai_audits"]
        assert info["limits"]["scans"] == _UNLIMITED["scans"]
        assert info["limits"]["emails_sent"] == _UNLIMITED["emails_sent"]

    def test_fresh_user_has_all_zero_usage(self, db, free_user):
        info = get_quota_info(db, free_user)

        assert info["usage"]["ai_audits"] == 0
        assert info["usage"]["scans"] == 0
        assert info["usage"]["emails_sent"] == 0

    def test_usage_reflects_actual_db_counters(self, db, free_user):
        _seed_usage(db, free_user, month=_MONTH, ai_audits=7, scans=3, emails_sent=15)

        with patch("app.quota_service._current_month", return_value=_MONTH):
            info = get_quota_info(db, free_user)

        assert info["usage"]["ai_audits"] == 7
        assert info["usage"]["scans"] == 3
        assert info["usage"]["emails_sent"] == 15

    def test_month_key_matches_current_month(self, db, free_user):
        with patch("app.quota_service._current_month", return_value=_MONTH):
            info = get_quota_info(db, free_user)

        assert info["month"] == _MONTH
