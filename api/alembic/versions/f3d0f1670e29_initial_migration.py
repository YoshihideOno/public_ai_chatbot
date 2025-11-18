"""initial_migration

Revision ID: f3d0f1670e29
Revises: 03b760e5716a
Create Date: 2025-10-18 12:42:18.149649

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = 'f3d0f1670e29'
down_revision = '03b760e5716a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 互換性維持のための拡張機能有効化のみを実行
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # スキーマの実体は別リビジョンで管理しているため何もしない
    pass
