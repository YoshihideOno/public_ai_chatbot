"""
テナントサービス単体テストファイル

このファイルはTenantServiceのビジネスロジックをテストします。
"""

import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.tenant_service import TenantService
from app.models.tenant import Tenant
from app.schemas.tenant import TenantStatus
from app.models.user import User, UserRole
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_get_by_id_success(db_session: AsyncSession):
    """
    正常系テスト: テナントIDでテナント情報取得
    """
    # テストデータ作成
    tenant = Tenant(
        name="Test Tenant",
        domain=f"test-tenant-{uuid.uuid4()}",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    try:
        service = TenantService(db_session)
        result = await service.get_by_id(str(tenant.id))
        
        assert result is not None
        assert result.id == tenant.id
        assert result.name == tenant.name
    finally:
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_session: AsyncSession):
    """
    異常系テスト: 存在しないテナントIDで取得
    """
    service = TenantService(db_session)
    fake_id = str(uuid.uuid4())
    result = await service.get_by_id(fake_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_by_domain_success(db_session: AsyncSession):
    """
    正常系テスト: ドメイン名でテナント情報取得
    """
    domain = f"test-domain-{uuid.uuid4()}"
    tenant = Tenant(
        name="Test Tenant",
        domain=domain,
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    try:
        service = TenantService(db_session)
        result = await service.get_by_domain(domain)
        
        assert result is not None
        assert result.domain == domain
    finally:
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
async def test_validate_tenant_access_success(db_session: AsyncSession):
    """
    正常系テスト: テナントアクセス権限検証
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
    
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        email=f"test-{unique_id}@example.com",
        username=f"testuser{unique_id}",  # 20文字以内
        hashed_password=get_password_hash("TestPassword1"),
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        service = TenantService(db_session)
        result = await service.validate_tenant_access(str(tenant.id), str(user.id))
        
        assert result is True
    finally:
        await db_session.delete(user)
        await db_session.delete(tenant)
        await db_session.commit()


@pytest.mark.asyncio
async def test_validate_tenant_access_failed(db_session: AsyncSession):
    """
    異常系テスト: テナントアクセス権限検証失敗
    """
    # テナント1とテナント2を作成
    tenant1 = Tenant(
        name="Test Tenant 1",
        domain=f"test-tenant1-{uuid.uuid4()}",
        status=TenantStatus.ACTIVE
    )
    tenant2 = Tenant(
        name="Test Tenant 2",
        domain=f"test-tenant2-{uuid.uuid4()}",
        status=TenantStatus.ACTIVE
    )
    db_session.add(tenant1)
    db_session.add(tenant2)
    await db_session.commit()
    await db_session.refresh(tenant1)
    await db_session.refresh(tenant2)
    
    # テナント1に所属するユーザーを作成
    user = User(
        email=f"test-{uuid.uuid4()}@example.com",
        username=f"testuser{uuid.uuid4()}",
        hashed_password=get_password_hash("TestPassword1"),
        role=UserRole.TENANT_ADMIN,
        tenant_id=tenant1.id,
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    try:
        service = TenantService(db_session)
        # テナント2へのアクセス権限を検証（失敗するはず）
        result = await service.validate_tenant_access(str(tenant2.id), str(user.id))
        
        assert result is False
    finally:
        await db_session.delete(user)
        await db_session.delete(tenant1)
        await db_session.delete(tenant2)
        await db_session.commit()

