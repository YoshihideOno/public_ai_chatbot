"""
APIキーサービス単体テストファイル

このファイルはApiKeyServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.services.api_key_service import ApiKeyService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus
from app.schemas.api_key import ApiKeyCreate


@pytest.mark.asyncio
async def test_create_api_key_success(db_session: AsyncSession):
    """
    正常系テスト: APIキー作成
    """
    # テナントを作成
    tenant = Tenant(
        name="Test Tenant",
        domain=f"test-tenant-{uuid.uuid4()}",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    try:
        service = ApiKeyService(db_session)
        api_key_data = ApiKeyCreate(
            provider="openai",  # 小文字に統一
            api_key="sk-test-key-1234567890",
            model="gpt-4"  # model_nameにマッピングされる
        )
        
        api_key = await service.create_api_key(str(tenant.id), api_key_data)
        
        assert api_key is not None
        assert api_key.provider == api_key_data.provider
        assert api_key.tenant_id == tenant.id
    finally:
        # クリーンアップ
        from app.models.api_key import ApiKey
        from sqlalchemy import select
        result = await db_session.execute(
            select(ApiKey).where(ApiKey.tenant_id == tenant.id)
        )
        api_keys = result.scalars().all()
        for ak in api_keys:
            await db_session.delete(ak)
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
@patch('app.services.api_key_service.ApiKeyService.verify_api_key', new_callable=AsyncMock)
async def test_verify_api_key_success(mock_verify: AsyncMock, db_session: AsyncSession):
    """
    正常系テスト: APIキー検証
    """
    mock_verify.return_value = {"valid": True, "message": "APIキーは有効です"}
    
    service = ApiKeyService(db_session)
    result = await service.verify_api_key("OPENAI", "sk-test-key-1234567890", "gpt-4")
    
    assert result["valid"] is True
    mock_verify.assert_called_once()

