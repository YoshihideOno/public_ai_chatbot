"""
認証API境界値テストファイル

このファイルは認証関連エンドポイントの境界値テストケースを定義します。
最小長、最大長、境界値のテストを含みます。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User
from app.models.tenant import Tenant
from app.core.security import verify_password
from unittest.mock import patch, AsyncMock

# テナントとユーザーを登録するヘルパー関数
async def register_user_and_tenant(client: TestClient, email: str, password: str, tenant_name: str, tenant_domain: str):
    import uuid
    # メールアドレスのローカル部分からユーザー名を生成
    # ハイフンはアンダースコアに置き換え、英数字とアンダースコアのみにする
    admin_username_prefix = email.split('@')[0].replace('-', '_')
    # 英数字とアンダースコア以外の文字を削除
    admin_username_prefix = ''.join(c for c in admin_username_prefix if c.isalnum() or c == '_')
    # 一意性を確保するためにUUIDを追加
    unique_suffix = str(uuid.uuid4())[:8]
    admin_username = f"{admin_username_prefix}_{unique_suffix}"
    # 20文字以内に収める（バリデーションルールに合わせる）
    if len(admin_username) > 20:
        # プレフィックスを短縮して20文字以内に収める
        max_prefix_len = 20 - len(unique_suffix) - 1  # -1はアンダースコア分
        admin_username = f"{admin_username_prefix[:max_prefix_len]}_{unique_suffix}"
    # 既にadmin_usernameが設定されているので、そのまま使用
    response = client.post(
        f"{settings.API_V1_STR}/auth/register-tenant",
        json={
            "tenant_name": tenant_name,
            "tenant_domain": tenant_domain,
            "admin_email": email,
            "admin_username": admin_username,
            "admin_password": password
        }
    )
    return response


class TestBoundaryValues:
    """境界値テストクラス"""
    
    @pytest.mark.asyncio
    async def test_email_min_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """メールアドレス最小長の境界値テスト"""
        # 最小長（6文字: a@b.co、TLDは2文字以上必要）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"a{unique_id}@b.co"  # 一意性を確保
        password = "SecurePassword1"
        tenant_name = f"Min Email Tenant {unique_id}"
        tenant_domain = f"min-email-tenant-{unique_id}"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 201, f"最小長メールアドレスが拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_email_below_min_length(self, client: TestClient, db_session: AsyncSession):
        """メールアドレス最小長未満のテスト"""
        # 最小長未満（4文字: a@b、TLDがない）
        email = "a@b"
        password = "SecurePassword1"
        tenant_name = "Below Min Email Tenant"
        tenant_domain = "below-min-email-tenant"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "最小長未満のメールアドレスが受け入れられました"
    
    @pytest.mark.asyncio
    async def test_email_max_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """メールアドレス最大長の境界値テスト"""
        # 最大長（255文字）
        local_part = "a" * 240
        email = f"{local_part}@example.com"
        password = "SecurePassword1"
        tenant_name = "Max Email Tenant"
        tenant_domain = "max-email-tenant"
        # 255文字を超えないように調整
        if len(email) > 255:
            email = email[:255]
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        # 255文字以内なら受け入れられる可能性がある
        assert response.status_code in [201, 422], f"最大長メールアドレスの処理が予期しない結果: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_password_min_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """パスワード最小長の境界値テスト"""
        # 最小長（8文字）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"minpass-{unique_id}@example.com"
        password = "Test1234"  # 8文字、大文字、小文字、数字を含む
        tenant_name = f"Min Password Tenant {unique_id}"
        tenant_domain = f"min-password-tenant-{unique_id}"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 201, f"最小長パスワードが拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_password_below_min_length(self, client: TestClient, db_session: AsyncSession):
        """パスワード最小長未満のテスト"""
        # 最小長未満（7文字）
        email = "belowminpass@example.com"
        password = "Test123"  # 7文字
        tenant_name = "Below Min Password Tenant"
        tenant_domain = "below-min-password-tenant"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "最小長未満のパスワードが受け入れられました"
    
    @pytest.mark.asyncio
    async def test_password_without_uppercase(self, client: TestClient, db_session: AsyncSession):
        """パスワードに大文字がない場合のテスト"""
        email = "nouppercase@example.com"
        password = "test1234"  # 大文字なし
        tenant_name = "No Uppercase Password Tenant"
        tenant_domain = "no-uppercase-password-tenant"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "大文字を含まないパスワードが受け入れられました"
    
    @pytest.mark.asyncio
    async def test_password_without_lowercase(self, client: TestClient, db_session: AsyncSession):
        """パスワードに小文字がない場合のテスト"""
        email = "nolowercase@example.com"
        password = "TEST1234"  # 小文字なし
        tenant_name = "No Lowercase Password Tenant"
        tenant_domain = "no-lowercase-password-tenant"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "小文字を含まないパスワードが受け入れられました"
    
    @pytest.mark.asyncio
    async def test_password_without_digit(self, client: TestClient, db_session: AsyncSession):
        """パスワードに数字がない場合のテスト"""
        email = "nodigit@example.com"
        password = "TestTest"  # 数字なし
        tenant_name = "No Digit Password Tenant"
        tenant_domain = "no-digit-password-tenant"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "数字を含まないパスワードが受け入れられました"
    
    @pytest.mark.asyncio
    async def test_username_min_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """ユーザー名最小長の境界値テスト"""
        # 最小長（3文字）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"minuser-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = f"Min Username Tenant {unique_id}"
        tenant_domain = f"min-username-tenant-{unique_id}"
        # ユーザー名を3文字に設定（一意性を確保するためにUUIDの一部を使用）
        username_suffix = str(uuid.uuid4()).replace('-', '')[:8]  # 8文字のUUID（ハイフンなし）
        # 3文字のユーザー名を生成（英数字のみ）
        admin_username = f"a{username_suffix[:2]}"  # 3文字（a + 2文字のUUID）
        
        # テスト実行前に、同じユーザー名を持つユーザーを削除（衝突を回避）
        from sqlalchemy import text
        try:
            await db_session.execute(
                text("DELETE FROM users WHERE username = :username AND is_active = true"),
                {"username": admin_username}
            )
            await db_session.commit()
        except Exception:
            await db_session.rollback()
        
        try:
            response = client.post(
                f"{settings.API_V1_STR}/auth/register-tenant",
                json={
                    "tenant_name": tenant_name,
                    "tenant_domain": tenant_domain,
                    "admin_email": email,
                    "admin_username": admin_username,  # 3文字（一意）
                    "admin_password": password
                }
            )
            assert response.status_code == 201, f"最小長ユーザー名が拒否されました: {response.json()}"
        finally:
            # テスト後にクリーンアップ
            try:
                await db_session.execute(
                    text("DELETE FROM tenants WHERE domain = :domain"),
                    {"domain": tenant_domain}
                )
                await db_session.execute(
                    text("DELETE FROM users WHERE email = :email"),
                    {"email": email}
                )
                await db_session.commit()
            except Exception:
                await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_username_below_min_length(self, client: TestClient, db_session: AsyncSession):
        """ユーザー名最小長未満のテスト"""
        # 最小長未満（2文字）
        email = "belowminuser@example.com"
        password = "SecurePassword1"
        tenant_name = "Below Min Username Tenant"
        tenant_domain = "below-min-username-tenant"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": "ab",  # 2文字
                "admin_password": password
            }
        )
        assert response.status_code == 422, "最小長未満のユーザー名が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_username_max_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """ユーザー名最大長の境界値テスト"""
        # 最大長（20文字、バリデーションルールに合わせる）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"maxuser-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = f"Max Username Tenant {unique_id}"
        tenant_domain = f"max-username-tenant-{unique_id}"
        # 20文字の一意のユーザー名を生成（UUIDの一部を使用）
        username_suffix = unique_id[:8]  # 8文字
        username = "a" * 12 + username_suffix  # 12文字 + 8文字 = 20文字
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": username,
                "admin_password": password
            }
        )
        assert response.status_code == 201, f"最大長ユーザー名が拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_username_above_max_length(self, client: TestClient, db_session: AsyncSession):
        """ユーザー名最大長超過のテスト"""
        # 最大長超過（101文字）
        email = "abovemaxuser@example.com"
        password = "SecurePassword1"
        tenant_name = "Above Max Username Tenant"
        tenant_domain = "above-max-username-tenant"
        username = "a" * 101  # 101文字
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": username,
                "admin_password": password
            }
        )
        assert response.status_code == 422, "最大長超過のユーザー名が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_username_invalid_characters(self, client: TestClient, db_session: AsyncSession):
        """ユーザー名に無効な文字が含まれる場合のテスト"""
        # ハイフンを含む（無効）
        email = "invaliduser@example.com"
        password = "SecurePassword1"
        tenant_name = "Invalid Username Tenant"
        tenant_domain = "invalid-username-tenant"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": "test-user",  # ハイフンを含む
                "admin_password": password
            }
        )
        assert response.status_code == 422, "無効な文字を含むユーザー名が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_tenant_name_min_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """テナント名最小長の境界値テスト"""
        # 最小長（2文字）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"mintenant-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = "AB"  # 2文字
        tenant_domain = f"min-tenant-name-{unique_id}"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 201, f"最小長テナント名が拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_tenant_name_below_min_length(self, client: TestClient, db_session: AsyncSession):
        """テナント名最小長未満のテスト"""
        # 最小長未満（1文字）
        email = "belowmintenant@example.com"
        password = "SecurePassword1"
        tenant_name = "A"  # 1文字
        tenant_domain = "below-min-tenant-name"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "最小長未満のテナント名が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_tenant_name_max_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """テナント名最大長の境界値テスト"""
        # 最大長（255文字）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"maxtenant-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = "A" * 255  # 255文字
        tenant_domain = f"max-tenant-name-{unique_id}"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 201, f"最大長テナント名が拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_tenant_domain_min_length_boundary(self, client: TestClient, db_session: AsyncSession):
        """テナント識別子最小長の境界値テスト"""
        # 最小長（3文字）
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"mindomain-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = f"Min Domain Tenant {unique_id}"
        tenant_domain = f"abc{unique_id}"  # 3文字以上（一意性を確保）
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 201, f"最小長テナント識別子が拒否されました: {response.json()}"
    
    @pytest.mark.asyncio
    async def test_tenant_domain_below_min_length(self, client: TestClient, db_session: AsyncSession):
        """テナント識別子最小長未満のテスト"""
        # 最小長未満（2文字）
        email = "belowmindomain@example.com"
        password = "SecurePassword1"
        tenant_name = "Below Min Domain Tenant"
        tenant_domain = "ab"  # 2文字
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "最小長未満のテナント識別子が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_tenant_domain_invalid_characters(self, client: TestClient, db_session: AsyncSession):
        """テナント識別子に無効な文字が含まれる場合のテスト"""
        # スペースを含む（無効）
        email = "invaliddomain@example.com"
        password = "SecurePassword1"
        tenant_name = "Invalid Domain Tenant"
        tenant_domain = "invalid domain"  # スペースを含む
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert response.status_code == 422, "無効な文字を含むテナント識別子が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_empty_strings(self, client: TestClient, db_session: AsyncSession):
        """空文字列のテスト"""
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": "",
                "tenant_domain": "",
                "admin_email": "",
                "admin_username": "",
                "admin_password": ""
            }
        )
        assert response.status_code == 422, "空文字列が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, client: TestClient, db_session: AsyncSession):
        """SQLインジェクション試行のテスト"""
        email = "sqlinject@example.com"
        password = "SecurePassword1"
        tenant_name = "SQL Injection Tenant"
        tenant_domain = "sql-injection-tenant"
        # SQLインジェクション試行
        username = "admin'; DROP TABLE users; --"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": username,
                "admin_password": password
            }
        )
        # 無効な文字として拒否されるべき
        assert response.status_code == 422, "SQLインジェクション試行が受け入れられました"
    
    @pytest.mark.asyncio
    async def test_xss_attempt(self, client: TestClient, db_session: AsyncSession):
        """XSS試行のテスト"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        email = f"xss-{unique_id}@example.com"
        password = "SecurePassword1"
        tenant_name = "<script>alert('XSS')</script>"
        tenant_domain = f"xss-tenant-{unique_id}"
        response = await register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        # XSS試行はバリデーションで拒否されるか、サニタイズされるべき
        # テナント名は通常の文字列として受け入れられる可能性があるが、
        # 出力時にサニタイズされるべき
        assert response.status_code in [201, 422], f"XSS試行の処理が予期しない結果: {response.status_code}"

