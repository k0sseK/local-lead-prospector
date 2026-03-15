"""add share_token to leads

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-03-15 03:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a1b2c3"
down_revision: Union[str, None] = "c3d4e5f6a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column("share_token", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_leads_share_token", "leads", ["share_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_leads_share_token", table_name="leads")
    op.drop_column("leads", "share_token")
