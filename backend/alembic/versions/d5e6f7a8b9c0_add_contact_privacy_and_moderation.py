"""Add contact privacy and moderation fields

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-11-01 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('contact_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requester_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('requester_phone', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('owner_response', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key('fk_contact_requests_user_id', 'users', ['requester_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_contact_requests_requester_id'), ['requester_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_contact_requests_status'), ['status'], unique=False)

    with op.batch_alter_table('report_flags', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reporter_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(length=20), server_default='OPEN', nullable=False))
        batch_op.add_column(sa.Column('reviewed_by', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_foreign_key('fk_report_flags_reporter_id', 'users', ['reporter_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_report_flags_status'), ['status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('report_flags', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_report_flags_status'))
        batch_op.drop_constraint('fk_report_flags_reporter_id', type_='foreignkey')
        batch_op.drop_column('reviewed_at')
        batch_op.drop_column('reviewed_by')
        batch_op.drop_column('status')
        batch_op.drop_column('reporter_id')

    with op.batch_alter_table('contact_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_contact_requests_status'))
        batch_op.drop_index(batch_op.f('ix_contact_requests_requester_id'))
        batch_op.drop_constraint('fk_contact_requests_user_id', type_='foreignkey')
        batch_op.drop_column('responded_at')
        batch_op.drop_column('owner_response')
        batch_op.drop_column('requester_phone')
        batch_op.drop_column('requester_id')

