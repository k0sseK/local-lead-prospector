"""add saved_searches table

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-03-15 02:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a1b2"
down_revision: Union[str, None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("keyword", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("radius_km", sa.Float(), nullable=False, server_default="5.0"),
        sa.Column("limit", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("country_code", sa.String(length=2), nullable=False, server_default="pl"),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("schedule", sa.String(), nullable=False, server_default="manual"),
        sa.Column("auto_audit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_leads", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_searches_id", "saved_searches", ["id"], unique=False)
    op.create_index("ix_saved_searches_user_id", "saved_searches", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_saved_searches_user_id", table_name="saved_searches")
    op.drop_index("ix_saved_searches_id", table_name="saved_searches")
    op.drop_table("saved_searches")
