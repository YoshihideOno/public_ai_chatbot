"""
管理者ユーザー作成スクリプト

このスクリプトは、指定したメールアドレス・ユーザー名・パスワードで
プラットフォーム管理者（PLATFORM_ADMIN）ユーザーを1件作成します。

安全性:
- 入力値は最低限のバリデーションを実施
- 既存ユーザー重複チェック（メール/ユーザー名）
- エラーハンドリングと適切な終了コード

実行例:
  PYTHONPATH=api python api/scripts/create_platform_admin.py \
    --email "yoshihide.ono@gmail.com" \
    --username "Platform_Admin" \
    --password "P@ssw0rd"
"""

import argparse
import asyncio
import sys
from typing import Optional

from app.core.database import AsyncSessionLocal
# モデルのリレーション解決のため、関連モデルを事前にインポートしてマッパー登録
# 参照のみでOK（未使用警告は無視）
from app.models import tenant as _tenant  # noqa: F401
from app.models import user as _user  # noqa: F401
from app.models import file as _file  # noqa: F401
from app.models import chunk as _chunk  # noqa: F401
from app.models import chat as _chat  # noqa: F401
from app.models import verification_token as _verification_token  # noqa: F401
from app.models import api_key as _api_key  # noqa: F401
from app.models import reminder as _reminder  # noqa: F401
from app.models import audit_log as _audit_log  # noqa: F401
from app.models import usage_log as _usage_log  # noqa: F401
from app.models import billing as _billing  # noqa: F401
from app.models import conversation as _conversation  # noqa: F401
from app.models import indexing_job as _indexing_job  # noqa: F401
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.models.user import UserRole


async def create_platform_admin(email: str, username: str, password: str) -> None:
    """
    管理者ユーザー（PLATFORM_ADMIN）を作成
    
    引数:
        email: メールアドレス
        username: ユーザー名（3-20文字、英数字とアンダースコア）
        password: パスワード（8文字以上・大文字/小文字/数字を含む）
    戻り値:
        None（標準出力に結果を表示）
    """
    async with AsyncSessionLocal() as session:
        user_service = UserService(session)

        # 既存チェック
        existing_by_email = await user_service.get_by_email(email)
        if existing_by_email:
            print(f"既に登録済みのメールアドレスです: {email}")
            sys.exit(0)

        existing_by_username = await user_service.get_by_username(username)
        if existing_by_username:
            print(f"既に使用中のユーザー名です: {username}")
            sys.exit(1)

        # 作成
        user = await user_service.create_user(
            UserCreate(
                email=email,
                username=username,
                password=password,
                role=UserRole.PLATFORM_ADMIN,
                tenant_id=None,
            )
        )

        # is_activeはcreate_userでTrueになる。is_verifiedは明示的に有効化
        await user_service.verify_user(user.id)  # is_verified = True

        # 再取得して状態確認
        created = await user_service.get_by_id(user.id)
        if not created:
            print("ユーザー作成に失敗しました")
            sys.exit(2)

        print("管理者ユーザーを作成しました:")
        print(f"  id: {created.id}")
        print(f"  email: {created.email}")
        print(f"  username: {created.username}")
        print(f"  role: {created.role}")
        print(f"  is_active: {created.is_active}")
        print(f"  is_verified: {created.is_verified}")


def main(argv: Optional[list] = None) -> int:
    """
    エントリポイント
    
    引数:
        argv: コマンドライン引数
    戻り値:
        プロセス終了コード
    """
    parser = argparse.ArgumentParser(description="PLATFORM_ADMINユーザーを作成します")
    parser.add_argument("--email", required=True, help="メールアドレス")
    parser.add_argument("--username", required=True, help="ユーザー名")
    parser.add_argument("--password", required=True, help="パスワード")

    args = parser.parse_args(argv)

    try:
        asyncio.run(create_platform_admin(args.email, args.username, args.password))
        return 0
    except SystemExit as e:
        return int(e.code)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


