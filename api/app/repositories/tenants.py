from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.tenant import Tenant
from .base import BaseRepository


class TenantRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        res = await self.session.execute(select(Tenant).where(Tenant.id == tenant_id))
        return res.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Optional[Tenant]:
        res = await self.session.execute(select(Tenant).where(Tenant.domain == domain))
        return res.scalar_one_or_none()

    async def create(self, tenant: Tenant) -> Tenant:
        self.session.add(tenant)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant

    async def update(self, tenant: Tenant, **fields) -> Tenant:
        for k, v in fields.items():
            setattr(tenant, k, v)
        await self.session.commit()
        await self.session.refresh(tenant)
        return tenant


