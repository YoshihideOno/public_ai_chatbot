"""
課金サービス単体テストファイル

このファイルはBillingServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.billing_service import BillingService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus


@pytest.mark.asyncio
async def test_get_or_create_billing_info_success(db_session: AsyncSession):
    """
    正常系テスト: 課金情報取得または作成
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
        service = BillingService(db_session)
        billing_info = await service.get_or_create_billing_info(
            str(tenant.id),
            "test@example.com"
        )
        
        # 課金情報が作成または取得されたことを確認
        assert billing_info is not None
    finally:
        # クリーンアップ: BillingInfoを先に削除
        from app.models.billing import BillingInfo
        from sqlalchemy import select
        billing_result = await db_session.execute(
            select(BillingInfo).where(BillingInfo.tenant_id == tenant.id)
        )
        billing_to_delete = billing_result.scalar_one_or_none()
        if billing_to_delete:
            await db_session.delete(billing_to_delete)
        await db_session.delete(tenant)
        await db_session.commit()

