"""
テナントのウィジェット許可オリジンカラム追加マイグレーション

このマイグレーションでは、テナントごとにウィジェット設置を許可する
オリジン（ドメイン）を管理するためのカラムを追加します。

allowed_widget_origins カラムには CSV 形式の文字列
（例: "https://foo.com,https://bar.example.com"）を保存します。
アプリケーション側で分割してリストとして扱います。
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Alembic revision identifiers, used by Alembic.
revision: str = "7f8e9d0c1b2a"
# 注意:
# - もともと "4b9f2a1c0b2a" を down_revision としていましたが、
#   すでに "ef3cc2e2afca" が "4b9f2a1c0b2a" と "aad8ed256fe4" を
#   マージする merge head となっているため、このリビジョンが
#   直接 "4b9f2a1c0b2a" から分岐すると複数 head が発生します。
# - そのため、このマイグレーションは最新の統合済み head
#   "ef3cc2e2afca" を継承するように変更し、履歴を一本化します。
down_revision: Union[str, None] = "ef3cc2e2afca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    テナントテーブルに allowed_widget_origins カラムを追加します。
    
    カラムはNULL許可とし、既存レコードには影響を与えません。
    値はCSV形式の文字列として保存されます。
    """
    op.add_column(
        "tenants",
        sa.Column("allowed_widget_origins", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """
    allowed_widget_origins カラムを削除します。
    
    ロールバック時にのみ使用されます。
    """
    op.drop_column("tenants", "allowed_widget_origins")


