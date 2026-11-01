"""Add report_images table for photo uploads

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-11-01 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'report_images',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('storage_path', sa.String(length=255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False, server_default='image/webp'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_images_report_id'), 'report_images', ['report_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_report_images_report_id'), table_name='report_images')
    op.drop_table('report_images')

