"""
テナント管理APIテストファイル

このファイルはテナント管理関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import get_password_hash
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
async def test_get_tenants_list_platform_admin(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: Platform Adminがテナント一覧取得
    """
    # Platform Adminユーザーを作成
    unique_id = str(uuid.uuid4())[:8]
    email = f"platform-admin-{unique_id}@example.com"
    username = f"platformadmin{unique_id}"
    password = "PlatformAdminPassword1"
    
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
        # テスト前に、test_rls_and_search.pyで作成されたテナントをクリーンアップ
        from sqlalchemy import text
        try:
            # 関連するユーザーとチャンク、ファイルを先に削除
            await db_session.execute(text("""
                DELETE FROM chunks WHERE tenant_id IN (
                    SELECT id FROM tenants WHERE name IN ('T', 'A', 'B') OR domain LIKE '%.example'
                )
            """))
            await db_session.execute(text("""
                DELETE FROM files WHERE tenant_id IN (
                    SELECT id FROM tenants WHERE name IN ('T', 'A', 'B') OR domain LIKE '%.example'
                )
            """))
            await db_session.execute(text("""
                DELETE FROM users WHERE tenant_id IN (
                    SELECT id FROM tenants WHERE name IN ('T', 'A', 'B') OR domain LIKE '%.example'
                )
            """))
            await db_session.execute(text("DELETE FROM tenants WHERE name IN ('T', 'A', 'B') OR domain LIKE '%.example'"))
            await db_session.commit()
        except Exception:
            # クリーンアップに失敗してもテストは続行
            await db_session.rollback()
            pass
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント一覧取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        # ユーザーを削除する前に、関連するテーブルもクリーンアップ
        from sqlalchemy import text
        try:
            await db_session.execute(text("DELETE FROM verification_tokens WHERE user_id = cast(:uid as uuid)"), {"uid": str(user.id)})
            await db_session.execute(text("DELETE FROM users WHERE id = cast(:uid as uuid)"), {"uid": str(user.id)})
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            # ユーザーが既に削除されている場合は無視
            pass


@pytest.mark.asyncio
async def test_get_tenants_list_non_admin_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 非Platform Adminがテナント一覧取得を試行
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"tenant-admin-{unique_id}@example.com"
    password = "TenantAdminPassword1"
    tenant_name = f"Tenant Admin Tenant {unique_id}"
    tenant_domain = f"tenant-admin-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント一覧取得を試行（403エラーになるはず）
        response = client.get(
            f"{settings.API_V1_STR}/tenants/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 403
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_detail_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナント詳細取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"get-tenant-{unique_id}@example.com"
    password = "GetTenantPassword1"
    tenant_name = f"Get Tenant {unique_id}"
    tenant_domain = f"get-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント詳細取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == tenant_id
        assert data["name"] == tenant_name
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_detail_not_found(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 存在しないテナントIDで詳細取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"notfound-tenant-{unique_id}@example.com"
    password = "NotFoundTenantPassword1"
    tenant_name = f"NotFound Tenant {unique_id}"
    tenant_domain = f"notfound-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        fake_tenant_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{fake_tenant_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # 存在しないテナントIDの場合、認可エラー（403）または404が返される
        assert response.status_code in [403, 404]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_embed_snippet_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 埋め込みスニペット取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"embed-{unique_id}@example.com"
    password = "EmbedPassword1"
    tenant_name = f"Embed Tenant {unique_id}"
    tenant_domain = f"embed-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # 埋め込みスニペット取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/embed-snippet",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "snippet" in data or "embed_code" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_tenant_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナント更新
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"update-tenant-{unique_id}@example.com"
    password = "UpdateTenantPassword1"
    tenant_name = f"Update Tenant {unique_id}"
    tenant_domain = f"update-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント更新
        new_name = f"Updated Tenant {unique_id}"
        response = client.put(
            f"{settings.API_V1_STR}/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"name": new_name}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_delete_tenant_platform_admin(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: Platform Adminがテナント削除
    """
    # Platform Adminユーザーを作成
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"platform-admin-delete-{unique_id}@example.com"
    admin_username = f"platformadmindelete{unique_id}"
    admin_password = "PlatformAdminDeletePassword1"
    
    admin_user = User(
        email=admin_email,
        username=admin_username,
        hashed_password=get_password_hash(admin_password),
        role=UserRole.PLATFORM_ADMIN,
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    # 削除対象のテナントを作成
    tenant_email = f"delete-target-{unique_id}@example.com"
    tenant_password = "DeleteTargetPassword1"
    tenant_name = f"Delete Target Tenant {unique_id}"
    tenant_domain = f"delete-target-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, tenant_email, tenant_password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, admin_token = get_authenticated_client(client, admin_email, admin_password)
        
        # テナント削除
        response = client.delete(
            f"{settings.API_V1_STR}/tenants/{tenant_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "削除" in response.json()["message"] or "deleted" in response.json()["message"].lower()
    finally:
        await db_session.delete(admin_user)
        await db_session.commit()
        await cleanup_test_data(db_session, tenant_email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナント統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"stats-tenant-{unique_id}@example.com"
    password = "StatsTenantPassword1"
    tenant_name = f"Stats Tenant {unique_id}"
    tenant_domain = f"stats-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント統計取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/stats",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # TenantStatsスキーマにはtenant_idやidフィールドがないため、他のフィールドを確認
        assert "total_users" in data or "active_users" in data or "storage_used_mb" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_tenant_settings_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナント設定更新
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"settings-tenant-{unique_id}@example.com"
    password = "SettingsTenantPassword1"
    tenant_name = f"Settings Tenant {unique_id}"
    tenant_domain = f"settings-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント設定更新
        response = client.put(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/settings",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"default_model": "gpt-4"}
        )
        assert response.status_code == 200
        assert "更新" in response.json()["message"] or "updated" in response.json()["message"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_regenerate_api_key_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー再発行
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"regenerate-api-{unique_id}@example.com"
    password = "RegenerateApiPassword1"
    tenant_name = f"Regenerate API Tenant {unique_id}"
    tenant_domain = f"regenerate-api-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # APIキー再発行
        response = client.post(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/regenerate-api-key",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_users_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナントユーザー一覧取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"users-tenant-{unique_id}@example.com"
    password = "UsersTenantPassword1"
    tenant_name = f"Users Tenant {unique_id}"
    tenant_domain = f"users-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナントユーザー一覧取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/users",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_usage_summary_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: テナント使用量サマリ取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"usage-tenant-{unique_id}@example.com"
    password = "UsageTenantPassword1"
    tenant_name = f"Usage Tenant {unique_id}"
    tenant_domain = f"usage-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code == 201
        tenant_id = register_response.json().get("tenant_id")
        
        _, access_token = get_authenticated_client(client, email, password)
        
        # テナント使用量サマリ取得
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id}/usage-summary",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 使用量サマリの構造を確認（実装による）
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_tenant_cross_tenant_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 他テナントのテナント情報取得試行
    """
    # テナント1のユーザーを作成
    unique_id1 = str(uuid.uuid4())[:8]
    email1 = f"tenant1-{unique_id1}@example.com"
    password1 = "Tenant1Password1"
    tenant_name1 = f"Tenant 1 {unique_id1}"
    tenant_domain1 = f"tenant1-{unique_id1}"
    
    # テナント2のユーザーを作成
    unique_id2 = str(uuid.uuid4())[:8]
    email2 = f"tenant2-{unique_id2}@example.com"
    password2 = "Tenant2Password1"
    tenant_name2 = f"Tenant 2 {unique_id2}"
    tenant_domain2 = f"tenant2-{unique_id2}"
    
    try:
        # テナント1のユーザーとテナントを作成
        register_response1 = register_user_and_tenant(client, email1, password1, tenant_name1, tenant_domain1)
        assert register_response1.status_code == 201
        tenant_id1 = register_response1.json().get("tenant_id")
        
        # テナント2のユーザーとテナントを作成
        register_response2 = register_user_and_tenant(client, email2, password2, tenant_name2, tenant_domain2)
        assert register_response2.status_code == 201
        tenant_id2 = register_response2.json().get("tenant_id")
        
        _, access_token2 = get_authenticated_client(client, email2, password2)
        
        # テナント2のユーザーがテナント1の情報を取得しようとする
        response = client.get(
            f"{settings.API_V1_STR}/tenants/{tenant_id1}",
            headers={"Authorization": f"Bearer {access_token2}"}
        )
        # 他テナントの情報は取得できない（403または404）
        assert response.status_code in [403, 404]
    finally:
        await cleanup_test_data(db_session, email1, tenant_domain1)
        await cleanup_test_data(db_session, email2, tenant_domain2)

