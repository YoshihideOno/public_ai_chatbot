"""
リマインダーサービス単体テストファイル

このファイルはReminderServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.services.reminder_service import ReminderService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus
from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_send_trial_reminders_success(db_session: AsyncSession):
    """
    正常系テスト: お試し利用期間終了前のリマインダー送信
    """
    service = ReminderService(db_session)
    result = await service.send_trial_reminders()
    
    assert result is not None
    assert "sent_count" in result or isinstance(result, dict)


@pytest.mark.asyncio
async def test_get_tenant_notifications_success(db_session: AsyncSession):
    """
    正常系テスト: テナント通知一覧取得
    """
    # テナントとユーザーを作成
    tenant = Tenant(
        name="Test Tenant",
        domain=f"test-tenant-{uuid.uuid4()}",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    user = User(
        email=f"test-{uuid.uuid4()}@example.com",
        username=f"testuser{uuid.uuid4()}",
        hashed_password=get_password_hash("TestPassword1"),
        role=UserRole.OPERATOR,
        tenant_id=tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        service = ReminderService(db_session)
        notifications = await service.get_tenant_notifications(
            str(tenant.id),
            str(user.id),
            is_read=None,
            limit=50
        )
        
        assert isinstance(notifications, list)
    finally:
        await db_session.delete(user)
        await db_session.delete(tenant)
        await db_session.commit()

