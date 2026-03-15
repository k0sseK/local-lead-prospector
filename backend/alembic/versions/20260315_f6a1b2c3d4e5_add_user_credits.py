"""add user credits columns

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-03-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a1b2c3d4e5'
down_revision = 'e5f6a1b2c3d4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('credits_balance', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('monthly_credits', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('credits_reset_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'credits_reset_at')
    op.drop_column('users', 'monthly_credits')
    op.drop_column('users', 'credits_balance')
