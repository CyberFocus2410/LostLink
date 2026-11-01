"""Add users, refresh_tokens tables and owner_id to reports

Revision ID: a1b2c3d4e5f6
Revises: 46eeb8853b51
Create Date: 2026-11-01 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '46eeb8853b51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users, refresh_tokens, and owner_id on reports."""

    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Refresh tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)

    # 3. Add nullable owner_id FK to reports (using batch_alter_table for SQLite compatibility)
    with op.batch_alter_table('reports') as batch_op:
        batch_op.add_column(
            sa.Column('owner_id', sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key('fk_reports_owner_id', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_reports_owner_id'), ['owner_id'], unique=False)


def downgrade() -> None:
    """Remove owner_id, refresh_tokens, and users."""
    with op.batch_alter_table('reports') as batch_op:
        batch_op.drop_index(batch_op.f('ix_reports_owner_id'))
        batch_op.drop_constraint('fk_reports_owner_id', type_='foreignkey')
        batch_op.drop_column('owner_id')

    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
