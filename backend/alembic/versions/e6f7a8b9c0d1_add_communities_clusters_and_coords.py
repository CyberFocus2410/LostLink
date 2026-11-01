"""Add communities, facility_clusters, and community_id, latitude, longitude to reports

Revision ID: e6f7a8b9c0d1
Revises: a1b2c3d4e5f6
Create Date: 2026-11-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Communities table
    op.create_table(
        'communities',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_communities_slug'), 'communities', ['slug'], unique=True)

    # 2. Facility clusters table
    op.create_table(
        'facility_clusters',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('community_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('aliases', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_facility_clusters_community_id'), 'facility_clusters', ['community_id'], unique=False)

    # 3. Add community_id, latitude, longitude to reports
    with op.batch_alter_table('reports') as batch_op:
        batch_op.add_column(sa.Column('community_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        batch_op.create_foreign_key('fk_reports_community_id', 'communities', ['community_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_reports_community_id'), ['community_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('reports') as batch_op:
        batch_op.drop_index(batch_op.f('ix_reports_community_id'))
        batch_op.drop_constraint('fk_reports_community_id', type_='foreignkey')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
        batch_op.drop_column('community_id')

    op.drop_index(op.f('ix_facility_clusters_community_id'), table_name='facility_clusters')
    op.drop_table('facility_clusters')

    op.drop_index(op.f('ix_communities_slug'), table_name='communities')
    op.drop_table('communities')

