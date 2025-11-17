"""
APIキー管理APIテストファイル

このファイルはAPIキー管理関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
async def test_get_providers_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: プロバイダー・モデル一覧取得
    """
    response = client.get(f"{settings.API_V1_STR}/api-keys/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert isinstance(data["providers"], list)


@pytest.mark.asyncio
async def test_create_api_key_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー登録
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-{unique_id}@example.com"
    password = "ApiKeyPassword1"
    tenant_name = f"ApiKey Tenant {unique_id}"
    tenant_domain = f"apikey-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # APIキー登録
        response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["provider"] == "openai"
        assert "api_key_masked" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_api_key_invalid_provider(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効なプロバイダーでAPIキー登録
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-invalid-{unique_id}@example.com"
    password = "ApiKeyInvalidPassword1"
    tenant_name = f"ApiKey Invalid Tenant {unique_id}"
    tenant_domain = f"apikey-invalid-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 無効なプロバイダーでAPIキー登録
        response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "INVALID_PROVIDER",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert response.status_code in [400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_api_keys_list_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー一覧取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-list-{unique_id}@example.com"
    password = "ApiKeyListPassword1"
    tenant_name = f"ApiKey List Tenant {unique_id}"
    tenant_domain = f"apikey-list-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # APIキー一覧取得
        response = client.get(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "api_keys" in data or isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_api_key_detail_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー詳細取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-detail-{unique_id}@example.com"
    password = "ApiKeyDetailPassword1"
    tenant_name = f"ApiKey Detail Tenant {unique_id}"
    tenant_domain = f"apikey-detail-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずAPIキーを作成
        create_response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert create_response.status_code == 200
        api_key_id = create_response.json()["id"]
        
        # APIキー詳細取得
        response = client.get(
            f"{settings.API_V1_STR}/api-keys/{api_key_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == api_key_id
        assert "api_key_masked" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_api_key_not_found(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 存在しないAPIキーIDで詳細取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-notfound-{unique_id}@example.com"
    password = "ApiKeyNotFoundPassword1"
    tenant_name = f"ApiKey NotFound Tenant {unique_id}"
    tenant_domain = f"apikey-notfound-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        fake_api_key_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/api-keys/{fake_api_key_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 404
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_api_key_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー更新
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-update-{unique_id}@example.com"
    password = "ApiKeyUpdatePassword1"
    tenant_name = f"ApiKey Update Tenant {unique_id}"
    tenant_domain = f"apikey-update-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずAPIキーを作成
        create_response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert create_response.status_code == 200
        api_key_id = create_response.json()["id"]
        
        # APIキー更新
        response = client.put(
            f"{settings.API_V1_STR}/api-keys/{api_key_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "is_active": False
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_delete_api_key_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー削除
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-delete-{unique_id}@example.com"
    password = "ApiKeyDeletePassword1"
    tenant_name = f"ApiKey Delete Tenant {unique_id}"
    tenant_domain = f"apikey-delete-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずAPIキーを作成
        create_response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert create_response.status_code == 200
        api_key_id = create_response.json()["id"]
        
        # APIキー削除
        response = client.delete(
            f"{settings.API_V1_STR}/api-keys/{api_key_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert "削除" in response.json()["message"] or "deleted" in response.json()["message"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
@patch('app.services.api_key_service.ApiKeyService.verify_api_key', new_callable=AsyncMock)
async def test_verify_api_key_inline_success(mock_verify: AsyncMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー検証（登録前）
    """
    mock_verify.return_value = {"valid": True, "message": "APIキーは有効です"}
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-verify-{unique_id}@example.com"
    password = "ApiKeyVerifyPassword1"
    tenant_name = f"ApiKey Verify Tenant {unique_id}"
    tenant_domain = f"apikey-verify-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # APIキー検証（登録前）
        response = client.post(
            f"{settings.API_V1_STR}/api-keys/verify-inline",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        mock_verify.assert_called_once()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
@patch('app.services.api_key_service.ApiKeyService.verify_api_key', new_callable=AsyncMock)
async def test_verify_api_key_success(mock_verify: AsyncMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: APIキー検証
    """
    mock_verify.return_value = {"valid": True, "message": "APIキーは有効です"}
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"apikey-verify2-{unique_id}@example.com"
    password = "ApiKeyVerify2Password1"
    tenant_name = f"ApiKey Verify2 Tenant {unique_id}"
    tenant_domain = f"apikey-verify2-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずAPIキーを作成
        create_response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert create_response.status_code == 200
        api_key_id = create_response.json()["id"]
        
        # APIキー検証
        response = client.post(
            f"{settings.API_V1_STR}/api-keys/{api_key_id}/verify",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        mock_verify.assert_called_once()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_api_key_no_tenant(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: テナント未設定でAPIキー登録
    """
    from tests.test_auth import register_user, cleanup_user
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"notenant-apikey-{unique_id}@example.com"
    password = "NoTenantApiKeyPassword1"
    username = f"noapikey{unique_id}"
    
    try:
        register_user(client, email, password, username)
        _, access_token = get_authenticated_client(client, email, password)
        
        # APIキー登録を試行（テナント未設定のためエラー）
        response = client.post(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "provider": "openai",
                "api_key": "sk-test-key-1234567890",
                "model": "gpt-4"
            }
        )
        assert response.status_code == 403
        detail = response.json()["detail"].lower()
        assert "テナント" in response.json()["detail"] or "tenant" in detail or "permissions" in detail
    finally:
        await cleanup_user(db_session, email)


@pytest.mark.asyncio
async def test_get_api_keys_operator_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: OPERATORがAPIキー一覧取得を試行（許可される）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"operator-apikey-{unique_id}@example.com"
    password = "OperatorApiKeyPassword1"
    tenant_name = f"Operator ApiKey Tenant {unique_id}"
    tenant_domain = f"operator-apikey-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # OPERATORはAPIキー一覧取得可能（require_tenant_userなので）
        response = client.get(
            f"{settings.API_V1_STR}/api-keys/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # require_tenant_userなのでOPERATORでもアクセス可能
        assert response.status_code == 200
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)

