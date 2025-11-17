"""make users email/username unique only when deleted_at is NULL

Revision ID: c143e943d08c
Revises: b1c2d3e4f5a6
Create Date: 2025-11-06 23:11:06.253920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c143e943d08c'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 既存のユニークインデックス（削除フラグ非考慮）を削除
    # 注意: 名前は初期マイグレーションの作成名に依存
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_username', table_name='users')

    # 削除されていない行（deleted_at IS NULL）のみにユニーク制約を適用する部分インデックスを作成
    op.execute(
        "CREATE UNIQUE INDEX uq_users_email_active ON users (email) WHERE deleted_at IS NULL;"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_users_username_active ON users (username) WHERE deleted_at IS NULL;"
    )


def downgrade() -> None:
    # 追加した部分ユニークインデックスを削除
    op.execute("DROP INDEX IF EXISTS uq_users_email_active;")
    op.execute("DROP INDEX IF EXISTS uq_users_username_active;")

    # 元のユニークインデックスを再作成
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
