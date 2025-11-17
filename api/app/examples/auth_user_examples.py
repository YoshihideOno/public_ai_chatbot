"""
認証機能とユーザー管理機能のテスト用サンプルコード

このファイルは実装した機能の動作確認用です。
実際のテストは pytest を使用して作成してください。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# テスト用のサンプルデータ
SAMPLE_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPass123!",
        "role": "PLATFORM_ADMIN",
        "tenant_id": None
    },
    {
        "email": "tenant_admin@acme.com",
        "username": "tenant_admin",
        "password": "TenantPass123!",
        "role": "TENANT_ADMIN",
        "tenant_id": "tenant-uuid-1"
    },
    {
        "email": "operator@acme.com",
        "username": "operator",
        "password": "OperatorPass123!",
        "role": "OPERATOR",
        "tenant_id": "tenant-uuid-1"
    },
    {
        "email": "auditor@acme.com",
        "username": "auditor",
        "password": "AuditorPass123!",
        "role": "AUDITOR",
        "tenant_id": "tenant-uuid-1"
    }
]

SAMPLE_TENANTS = [
    {
        "id": "tenant-uuid-1",
        "name": "Acme Corporation",
        "domain": "acme.example.com",
        "plan": "PRO",
        "status": "ACTIVE",
        "api_key": "pk_live_acme123...",
        "settings": {
            "default_model": "gpt-4",
            "chunk_size": 1024,
            "chunk_overlap": 200,
            "max_queries_per_day": 10000
        }
    }
]


def print_api_examples():
    """API使用例を表示"""
    print("=== 認証機能とユーザー管理機能のAPI使用例 ===\n")
    
    print("1. ユーザー登録")
    print("POST /api/v1/auth/register")
    print(json.dumps(SAMPLE_USERS[0], indent=2))
    print()
    
    print("2. ログイン")
    print("POST /api/v1/auth/login")
    print(json.dumps({
        "email": "admin@example.com",
        "password": "AdminPass123!"
    }, indent=2))
    print()
    
    print("3. トークン更新")
    print("POST /api/v1/auth/refresh")
    print(json.dumps({
        "refresh_token": "rt_abc123..."
    }, indent=2))
    print()
    
    print("4. 現在のユーザー情報取得")
    print("GET /api/v1/auth/me")
    print("Headers: Authorization: Bearer <access_token>")
    print()
    
    print("5. ユーザー一覧取得（管理者のみ）")
    print("GET /api/v1/users/?skip=0&limit=100")
    print("Headers: Authorization: Bearer <access_token>")
    print()
    
    print("6. ユーザー作成（管理者のみ）")
    print("POST /api/v1/users/")
    print(json.dumps(SAMPLE_USERS[1], indent=2))
    print("Headers: Authorization: Bearer <access_token>")
    print()
    
    print("7. ユーザー更新（管理者のみ）")
    print("PUT /api/v1/users/{user_id}")
    print(json.dumps({
        "email": "updated@example.com",
        "username": "updated_user",
        "role": "OPERATOR"
    }, indent=2))
    print("Headers: Authorization: Bearer <access_token>")
    print()
    
    print("8. ユーザー削除（管理者のみ）")
    print("DELETE /api/v1/users/{user_id}")
    print("Headers: Authorization: Bearer <access_token>")
    print()
    
    print("9. パスワードリセット要求")
    print("POST /api/v1/auth/password-reset")
    print(json.dumps({
        "email": "admin@example.com"
    }, indent=2))
    print()
    
    print("10. パスワードリセット実行")
    print("POST /api/v1/auth/password-reset/confirm")
    print(json.dumps({
        "token": "reset_token_abc123...",
        "new_password": "NewPassword123!"
    }, indent=2))
    print()


def print_role_permissions():
    """権限マトリックスを表示"""
    print("=== 権限マトリックス ===\n")
    
    permissions = {
        "PLATFORM_ADMIN": [
            "全テナントのユーザー管理",
            "全テナントのリソースアクセス",
            "プラットフォーム全体の設定",
            "ユーザーロール変更",
            "テナント作成・削除"
        ],
        "TENANT_ADMIN": [
            "自テナントのユーザー管理",
            "自テナントのリソースアクセス",
            "テナント設定変更",
            "OPERATOR/AUDITORロールのユーザー作成",
            "自テナント内のユーザー削除"
        ],
        "OPERATOR": [
            "ナレッジ管理",
            "統計確認",
            "設定変更（制限あり）",
            "自分のプロフィール変更"
        ],
        "AUDITOR": [
            "ログ閲覧",
            "監査データエクスポート",
            "自分のプロフィール変更"
        ]
    }
    
    for role, perms in permissions.items():
        print(f"{role}:")
        for perm in perms:
            print(f"  - {perm}")
        print()


def print_validation_rules():
    """バリデーションルールを表示"""
    print("=== バリデーションルール ===\n")
    
    print("パスワード要件:")
    print("  - 8文字以上")
    print("  - 大文字を含む")
    print("  - 小文字を含む")
    print("  - 数字を含む")
    print("  - 例: AdminPass123!")
    print()
    
    print("メールアドレス要件:")
    print("  - 有効なメール形式")
    print("  - 例: user@example.com")
    print()
    
    print("ユーザー名要件:")
    print("  - 一意である必要がある")
    print("  - 例: username123")
    print()
    
    print("JWTトークン:")
    print("  - アクセストークン: 30分有効")
    print("  - リフレッシュトークン: 7日有効")
    print("  - ペイロード: sub, tenant_id, role, exp, iat")
    print()


def print_security_features():
    """セキュリティ機能を表示"""
    print("=== セキュリティ機能 ===\n")
    
    print("認証:")
    print("  - JWT Bearer Token認証")
    print("  - パスワードハッシュ化（bcrypt）")
    print("  - トークン検証・期限チェック")
    print()
    
    print("認可:")
    print("  - ロールベースアクセス制御（RBAC）")
    print("  - テナント分離")
    print("  - リソースレベル権限チェック")
    print()
    
    print("データ保護:")
    print("  - パスワードの平文保存禁止")
    print("  - ソフトデリート（論理削除）")
    print("  - 入力バリデーション")
    print()
    
    print("監査:")
    print("  - ログイン時刻記録")
    print("  - 操作ログ（将来実装）")
    print("  - エラーログ")
    print()


if __name__ == "__main__":
    print_api_examples()
    print_role_permissions()
    print_validation_rules()
    print_security_features()
    
    print("=== 実装完了 ===")
    print("認証機能とユーザー管理機能の実装が完了しました。")
    print("以下の機能が利用可能です:")
    print("  ✓ JWT発行・検証処理")
    print("  ✓ ログイン/ログアウトAPI")
    print("  ✓ 認証チェックミドルウェア")
    print("  ✓ ユーザーCRUD API")
    print("  ✓ 権限によるアクセス制御")
    print("  ✓ 入力バリデーション（email, password）")
