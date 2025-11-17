"""
統計サービス単体テストファイル

このファイルはStatsServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.stats_service import StatsService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus


@pytest.mark.asyncio
async def test_get_usage_stats_success(db_session: AsyncSession):
    """
    正常系テスト: 利用統計取得
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
        service = StatsService(db_session)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        stats = await service.get_usage_stats(
            tenant_id=str(tenant.id),
            start_date=start_date,
            end_date=end_date,
            granularity="day"
        )
        
        assert stats is not None
        # statsはPydanticモデル（UsageStats）を返す
        assert hasattr(stats, 'tenant_id') or isinstance(stats, dict)
    finally:
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_storage_stats_success(db_session: AsyncSession):
    """
    正常系テスト: ストレージ統計取得
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
        service = StatsService(db_session)
        stats = await service.get_storage_stats(str(tenant.id))
        
        assert stats is not None
        # statsはPydanticモデル（UsageStats）を返す
        assert hasattr(stats, 'tenant_id') or isinstance(stats, dict)
    finally:
        await db_session.delete(tenant)
        await db_session.commit()

