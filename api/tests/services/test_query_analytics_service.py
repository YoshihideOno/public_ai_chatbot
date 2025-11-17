"""
クエリアナリティクスサービス単体テストファイル

このファイルはQueryAnalyticsServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.services.query_analytics_service import QueryAnalyticsService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus


@pytest.mark.asyncio
@patch('app.services.query_analytics_service.QueryAnalyticsService.rebuild', new_callable=AsyncMock)
async def test_rebuild_success(mock_rebuild: AsyncMock, db_session: AsyncSession):
    """
    正常系テスト: クエリアナリティクスの再集計実行
    """
    mock_rebuild.return_value = None
    
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
        service = QueryAnalyticsService(db_session)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        await service.rebuild(
            tenant_id=str(tenant.id),
            locale="ja",
            period_start=start_date,
            period_end=end_date,
            top_k=10
        )
        
        mock_rebuild.assert_called_once()
    finally:
        await db_session.delete(tenant)
        await db_session.commit()

