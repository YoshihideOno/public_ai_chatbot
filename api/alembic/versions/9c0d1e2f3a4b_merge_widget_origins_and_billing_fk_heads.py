"""
ウィジェット設置ドメインと課金関連テーブルのマイグレーションブランチ統合

このマイグレーションは、以下の2つのheadリビジョンを1つの履歴に統合するための
「mergeマイグレーション」です。

- 7f8e9d0c1b2a: テナントの allowed_widget_origins カラム追加
- 6d7e5dd7c2d0: billing_info.tenant_id 外部キー制約追加

スキーマ変更自体は既存マイグレーションで完了しているため、本ファイルでは
upgrade/downgrade ともに何も処理を行いません。
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401  # 将来の拡張に備えて残しておく
import sqlalchemy as sa  # noqa: F401


# Alembic revision identifiers, used by Alembic.
revision: str = "9c0d1e2f3a4b"
down_revision: Union[str, Sequence[str], None] = ("7f8e9d0c1b2a", "6d7e5dd7c2d0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    スキーマ変更は既存マイグレーションで完了しているため、ここでは何もしません。

    この関数の目的:
      - Alembicのマイグレーション履歴グラフ上で複数存在していたhead
        （7f8e9d0c1b2a, 6d7e5dd7c2d0）を1つに統合し、
        `alembic upgrade head` を正常に実行できるようにすること。
    引数:
      なし
    戻り値:
      なし
    """
    # 何も処理を行いません（merge専用リビジョン）
    return None


def downgrade() -> None:
    """
    downgrade時もスキーマ変更は行いません。

    このマイグレーションより前に戻る場合は、Alembicが自動的に
    7f8e9d0c1b2a および 6d7e5dd7c2d0 のいずれか、もしくは両方を
    適切な順序でロールバックします。

    引数:
      なし
    戻り値:
      なし
    """
    # 何も処理を行いません（merge専用リビジョン）
    return None


