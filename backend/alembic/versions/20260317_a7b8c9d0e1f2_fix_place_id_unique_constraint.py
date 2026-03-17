"""fix place_id unique constraint — make ix_leads_place_id non-unique

Revision ID: a7b8c9d0e1f2
Revises: f6a1b2c3d4e5
Create Date: 2026-03-17
"""
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the incorrectly-unique index and recreate as non-unique.
    # The per-user uniqueness is already enforced by uq_leads_user_place (user_id, place_id).
    op.drop_index("ix_leads_place_id", table_name="leads")
    op.create_index("ix_leads_place_id", "leads", ["place_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_leads_place_id", table_name="leads")
    op.create_index("ix_leads_place_id", "leads", ["place_id"], unique=True)
