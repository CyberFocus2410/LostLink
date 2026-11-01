"""Add composite indexes for PostgreSQL performance and concurrency

Revision ID: b3c4d5e6f7a8
Revises: e6f7a8b9c0d1
Create Date: 2026-11-01 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b3c4d5e6f7a8'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite indexes on reports table
    op.create_index('ix_reports_owner_status', 'reports', ['owner_id', 'status'])
    op.create_index('ix_reports_community_status', 'reports', ['community_id', 'status'])
    op.create_index('ix_reports_date_status', 'reports', ['event_date', 'status'])


def downgrade() -> None:
    op.drop_index('ix_reports_date_status', table_name='reports')
    op.drop_index('ix_reports_community_status', table_name='reports')
    op.drop_index('ix_reports_owner_status', table_name='reports')

