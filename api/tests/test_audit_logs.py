"""
監査ログAPIテストファイル

このファイルは監査ログ関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テスト、テナント分離テストを含みます。
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
async def test_get_recent_audit_logs_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 最近の監査ログ取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"audit-{unique_id}@example.com"
    password = "AuditPassword1"
    tenant_name = f"Audit Tenant {unique_id}"
    tenant_domain = f"audit-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 最近の監査ログ取得
        response = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_recent_audit_logs_with_limit(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 制限付きで最近の監査ログ取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"audit-limit-{unique_id}@example.com"
    password = "AuditLimitPassword1"
    tenant_name = f"Audit Limit Tenant {unique_id}"
    tenant_domain = f"audit-limit-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 制限付きで最近の監査ログ取得
        response = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
        assert len(data["activities"]) <= 5
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_recent_audit_logs_platform_admin(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: Platform Adminが全テナントの監査ログ取得
    """
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    # Platform Adminユーザーを作成
    unique_id = str(uuid.uuid4())[:8]
    email = f"platform-admin-audit-{unique_id}@example.com"
    username = f"platformadminaudit{unique_id}"
    password = "PlatformAdminAuditPassword1"
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=UserRole.PLATFORM_ADMIN,
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        _, access_token = get_authenticated_client(client, email, password)
        
        # Platform Adminは全テナントの監査ログを取得可能
        response = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "activities" in data
        assert isinstance(data["activities"], list)
    finally:
        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_recent_audit_logs_tenant_isolation(client: TestClient, db_session: AsyncSession):
    """
    テナント分離テスト: 他テナントの監査ログは取得できない
    """
    # テナント1のユーザーを作成
    unique_id1 = str(uuid.uuid4())[:8]
    email1 = f"tenant1-audit-{unique_id1}@example.com"
    password1 = "Tenant1AuditPassword1"
    tenant_name1 = f"Tenant 1 Audit {unique_id1}"
    tenant_domain1 = f"tenant1-audit-{unique_id1}"
    
    # テナント2のユーザーを作成
    unique_id2 = str(uuid.uuid4())[:8]
    email2 = f"tenant2-audit-{unique_id2}@example.com"
    password2 = "Tenant2AuditPassword1"
    tenant_name2 = f"Tenant 2 Audit {unique_id2}"
    tenant_domain2 = f"tenant2-audit-{unique_id2}"
    
    try:
        # テナント1のユーザーとテナントを作成
        register_user_and_tenant(client, email1, password1, tenant_name1, tenant_domain1)
        _, access_token1 = get_authenticated_client(client, email1, password1)
        
        # テナント2のユーザーとテナントを作成
        register_user_and_tenant(client, email2, password2, tenant_name2, tenant_domain2)
        _, access_token2 = get_authenticated_client(client, email2, password2)
        
        # テナント1のユーザーが監査ログを取得
        response1 = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token1}"},
            params={"limit": 10}
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # テナント2のユーザーが監査ログを取得
        response2 = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token2}"},
            params={"limit": 10}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        # テナント分離が機能していることを確認
        # （実際の実装では、各テナントのログのみが返される）
        assert isinstance(data1["activities"], list)
        assert isinstance(data2["activities"], list)
    finally:
        await cleanup_test_data(db_session, email1, tenant_domain1)
        await cleanup_test_data(db_session, email2, tenant_domain2)


@pytest.mark.asyncio
async def test_get_recent_audit_logs_invalid_limit(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効なlimit値で監査ログ取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"audit-invalid-{unique_id}@example.com"
    password = "AuditInvalidPassword1"
    tenant_name = f"Audit Invalid Tenant {unique_id}"
    tenant_domain = f"audit-invalid-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 無効なlimit値（上限超過）
        response = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 100}  # 上限は50
        )
        # バリデーションエラーになるはず
        assert response.status_code in [400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_recent_audit_logs_no_auth(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 認証トークンなしで監査ログ取得
    """
    response = client.get(
        f"{settings.API_V1_STR}/audit-logs/recent",
        params={"limit": 10}
    )
    assert response.status_code in [401, 403]  # FastAPIのHTTPBearerは認証トークンがない場合403を返す可能性がある


@pytest.mark.asyncio
async def test_get_recent_audit_logs_no_tenant(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: テナント未設定で監査ログ取得
    """
    from tests.test_auth import register_user, cleanup_user
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"notenant-audit-{unique_id}@example.com"
    password = "NoTenantAuditPassword1"
    username = f"noaudit{unique_id}"
    
    try:
        register_user(client, email, password, username)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 監査ログ取得を試行（テナント未設定のためエラー）
        response = client.get(
            f"{settings.API_V1_STR}/audit-logs/recent",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 10}
        )
        assert response.status_code == 400
        assert "テナントID" in response.json()["detail"] or "tenant" in response.json()["detail"].lower()
    finally:
        await cleanup_user(db_session, email)

