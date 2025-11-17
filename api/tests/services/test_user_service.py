"""
ユーザーサービス単体テストファイル

このファイルはUserServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession):
    """
    正常系テスト: ユーザー作成
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
        service = UserService(db_session)
        unique_id = str(uuid.uuid4())[:8]
        user_data = UserCreate(
            email=f"test-{unique_id}@example.com",
            username=f"testuser{unique_id}",
            password="TestPassword1",
            role=UserRole.OPERATOR,
            tenant_id=str(tenant.id)
        )
        
        user = await service.create_user(user_data)
        
        assert user is not None
        assert user.email == user_data.email
        assert user.username == user_data.username
        assert verify_password(user_data.password, user.hashed_password)
        assert user.tenant_id == tenant.id
    finally:
        # クリーンアップ
        from sqlalchemy import select
        user_result = await db_session.execute(
            select(User).where(User.email == user_data.email)
        )
        user_to_delete = user_result.scalar_one_or_none()
        if user_to_delete:
            await db_session.delete(user_to_delete)
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_email_success(db_session: AsyncSession):
    """
    正常系テスト: メールアドレスでユーザー取得
    """
    email = f"test-{uuid.uuid4()}@example.com"
    user = User(
        email=email,
            username=f"testuser{str(uuid.uuid4())[:8]}",
        hashed_password=get_password_hash("TestPassword1"),
        role=UserRole.OPERATOR,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        service = UserService(db_session)
        result = await service.get_by_email(email)
        
        assert result is not None
        assert result.email == email
    finally:
        await db_session.delete(user)
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_email_not_found(db_session: AsyncSession):
    """
    異常系テスト: 存在しないメールアドレスでユーザー取得
    """
    service = UserService(db_session)
    fake_email = f"fake-{uuid.uuid4()}@example.com"
    result = await service.get_by_email(fake_email)
    
    assert result is None


@pytest.mark.asyncio
async def test_verify_user_success(db_session: AsyncSession):
    """
    正常系テスト: ユーザー検証
    """
    user = User(
        email=f"test-{uuid.uuid4()}@example.com",
            username=f"testuser{str(uuid.uuid4())[:8]}",
        hashed_password=get_password_hash("TestPassword1"),
        role=UserRole.OPERATOR,
        is_active=True,
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        service = UserService(db_session)
        await service.verify_user(user.id)
        
        # 再取得して検証状態を確認
        await db_session.refresh(user)
        assert user.is_verified is True
    finally:
        await db_session.delete(user)
        await db_session.commit()

