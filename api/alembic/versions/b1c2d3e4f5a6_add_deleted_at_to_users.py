"""add deleted_at to users

Revision ID: b1c2d3e4f5a6
Revises: ef3cc2e2afca
Create Date: 2025-11-06 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1c2d3e4f5a6'
down_revision = 'ef3cc2e2afca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    usersテーブルにdeleted_atカラムを追加
    論理削除と非アクティブを区別するため
    """
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """
    usersテーブルからdeleted_atカラムを削除
    """
    op.drop_column('users', 'deleted_at')

