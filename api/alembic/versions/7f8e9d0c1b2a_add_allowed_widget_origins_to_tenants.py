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
down_revision: Union[str, None] = "4b9f2a1c0b2a"
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


