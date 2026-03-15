"""add email_events table

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-03-15 01:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_events",
        sa.Column("id", sa.String(length=36), nullable=False),   # UUID4 string
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("sequence_step_id", sa.Integer(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=False),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_events_user_id", "email_events", ["user_id"], unique=False)
    op.create_index("ix_email_events_lead_id", "email_events", ["lead_id"], unique=False)
    op.create_index("ix_email_events_sequence_step_id", "email_events", ["sequence_step_id"], unique=False)


def downgrade() -> None:
    op.drop_table("email_events")
