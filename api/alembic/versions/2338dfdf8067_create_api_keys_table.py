"""create_api_keys_table

Revision ID: 2338dfdf8067
Revises: c7d8e9f0a1b2
Create Date: 2025-11-15 17:13:23.332345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2338dfdf8067'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    api_keysテーブルを作成します。
    
    テナント毎のLLMプロバイダーAPIキー情報を管理するテーブルです。
    """
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('api_key', sa.String(length=500), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
    )
    op.create_index(op.f('ix_api_keys_tenant_id'), 'api_keys', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_api_keys_provider'), 'api_keys', ['provider'], unique=False)


def downgrade() -> None:
    """
    api_keysテーブルを削除します。
    """
    op.drop_index(op.f('ix_api_keys_provider'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_tenant_id'), table_name='api_keys')
    op.drop_table('api_keys')
