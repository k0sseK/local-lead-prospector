"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-15 00:00:00.000000

Creates all tables from scratch.  On a brownfield database (Railway production)
that was previously managed by create_all() + ALTER TABLE hacks, this migration
is never actually executed — migrate.py detects the existing schema and stamps
the DB at this revision instead of running the DDL.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("plan", sa.String(), nullable=True),
        sa.Column("plan_expires_at", sa.DateTime(), nullable=True),
        sa.Column("lemon_subscription_id", sa.String(), nullable=True),
        sa.Column("lemon_subscription_status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.Column("verification_token", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_lemon_subscription_id", "users", ["lemon_subscription_id"], unique=False)
    op.create_index("ix_users_verification_token", "users", ["verification_token"], unique=False)

    # ── user_settings ─────────────────────────────────────────────────────────
    op.create_table(
        "user_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("sender_name", sa.String(), nullable=True),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("offer_description", sa.Text(), nullable=True),
        sa.Column("tone_of_voice", sa.String(), nullable=True),
        sa.Column("email_provider", sa.String(), nullable=True),
        sa.Column("resend_api_key", sa.String(), nullable=True),
        sa.Column("smtp_host", sa.String(), nullable=True),
        sa.Column("smtp_port", sa.Integer(), nullable=True),
        sa.Column("smtp_user", sa.String(), nullable=True),
        sa.Column("smtp_password", sa.String(), nullable=True),
        sa.Column("smtp_from_email", sa.String(), nullable=True),
        sa.Column("default_email_language", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_settings_id", "user_settings", ["id"], unique=False)

    # ── monthly_usage ─────────────────────────────────────────────────────────
    op.create_table(
        "monthly_usage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("month", sa.String(length=7), nullable=False),
        sa.Column("ai_audits", sa.Integer(), nullable=True),
        sa.Column("scans", sa.Integer(), nullable=True),
        sa.Column("emails_sent", sa.Integer(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 5), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "month", name="uq_monthly_usage_user_month"),
    )
    op.create_index("ix_monthly_usage_id", "monthly_usage", ["id"], unique=False)
    op.create_index("ix_monthly_usage_user_id", "monthly_usage", ["user_id"], unique=False)

    # ── usage_events ──────────────────────────────────────────────────────────
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("tokens_in", sa.Integer(), nullable=True),
        sa.Column("tokens_out", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 5), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usage_events_id", "usage_events", ["id"], unique=False)
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"], unique=False)

    # ── audit_templates ───────────────────────────────────────────────────────
    op.create_table(
        "audit_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_templates_id", "audit_templates", ["id"], unique=False)
    op.create_index("ix_audit_templates_user_id", "audit_templates", ["user_id"], unique=False)

    # ── email_sequences ───────────────────────────────────────────────────────
    op.create_table(
        "email_sequences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_sequences_id", "email_sequences", ["id"], unique=False)
    op.create_index("ix_email_sequences_lead_id", "email_sequences", ["lead_id"], unique=False)
    op.create_index("ix_email_sequences_user_id", "email_sequences", ["user_id"], unique=False)

    # ── email_sequence_steps ──────────────────────────────────────────────────
    op.create_table(
        "email_sequence_steps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sequence_id", sa.Integer(), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("day_offset", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["sequence_id"], ["email_sequences.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_sequence_steps_id", "email_sequence_steps", ["id"], unique=False)
    op.create_index("ix_email_sequence_steps_sequence_id", "email_sequence_steps", ["sequence_id"], unique=False)

    # ── leads ─────────────────────────────────────────────────────────────────
    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("place_id", sa.String(), nullable=True),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("website_uri", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("has_ssl", sa.Boolean(), nullable=True),
        sa.Column("audited", sa.Boolean(), nullable=True),
        sa.Column("audit_report", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("lead_score", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "place_id", name="uq_leads_user_place"),
    )
    op.create_index("ix_leads_id", "leads", ["id"], unique=False)
    op.create_index("ix_leads_place_id", "leads", ["place_id"], unique=False)
    op.create_index("ix_leads_company_name", "leads", ["company_name"], unique=False)
    op.create_index("ix_leads_user_id", "leads", ["user_id"], unique=False)

    # ── PostgreSQL-specific: pg_trgm extension + GIN index for fast ILIKE ─────
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        op.execute(
            "CREATE INDEX IF NOT EXISTS idx_leads_company_trgm "
            "ON leads USING GIN (company_name gin_trgm_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS idx_leads_company_trgm")

    op.drop_table("leads")
    op.drop_table("email_sequence_steps")
    op.drop_table("email_sequences")
    op.drop_table("audit_templates")
    op.drop_table("usage_events")
    op.drop_table("monthly_usage")
    op.drop_table("user_settings")
    op.drop_table("users")
