"""add query analytics tables

Revision ID: 4b9f2a1c0b2a
Revises: ae01f2ea5e65
Create Date: 2025-11-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4b9f2a1c0b2a'
down_revision = 'ae01f2ea5e65'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 必要拡張（ローカル開発環境で未有効の場合）
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # query_clusters
    op.create_table(
        'query_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('sample_queries', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'locale', 'period_start', 'period_end', 'cluster_id', name='uq_query_clusters_scope_cluster')
    )
    op.create_index('ix_query_clusters_tenant', 'query_clusters', ['tenant_id'])
    op.create_index('ix_query_clusters_locale', 'query_clusters', ['locale'])
    op.create_index('ix_query_clusters_period_start', 'query_clusters', ['period_start'])
    op.create_index('ix_query_clusters_period_end', 'query_clusters', ['period_end'])

    # top_query_aggregates
    op.create_table(
        'top_query_aggregates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('locale', sa.String(length=10), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.Column('like_rate', sa.Numeric(4, 3), nullable=False),
        sa.Column('avg_response_time_ms', sa.Numeric(), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'locale', 'period_start', 'period_end', 'rank', name='uq_top_query_aggregates_scope_rank')
    )
    op.create_index('ix_top_query_aggregates_tenant', 'top_query_aggregates', ['tenant_id'])
    op.create_index('ix_top_query_aggregates_locale', 'top_query_aggregates', ['locale'])
    op.create_index('ix_top_query_aggregates_period_start', 'top_query_aggregates', ['period_start'])
    op.create_index('ix_top_query_aggregates_period_end', 'top_query_aggregates', ['period_end'])


def downgrade() -> None:
    op.drop_index('ix_top_query_aggregates_period_end', table_name='top_query_aggregates')
    op.drop_index('ix_top_query_aggregates_period_start', table_name='top_query_aggregates')
    op.drop_index('ix_top_query_aggregates_locale', table_name='top_query_aggregates')
    op.drop_index('ix_top_query_aggregates_tenant', table_name='top_query_aggregates')
    op.drop_table('top_query_aggregates')

    op.drop_index('ix_query_clusters_period_end', table_name='query_clusters')
    op.drop_index('ix_query_clusters_period_start', table_name='query_clusters')
    op.drop_index('ix_query_clusters_locale', table_name='query_clusters')
    op.drop_index('ix_query_clusters_tenant', table_name='query_clusters')
    op.drop_table('query_clusters')


