from __future__ import annotations

from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.file import File
from .base import BaseRepository


class FileRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get(self, file_id: str) -> Optional[File]:
        res = await self.session.execute(select(File).where(File.id == file_id))
        return res.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: str, limit: int = 50, offset: int = 0) -> Sequence[File]:
        await self.set_tenant_context(tenant_id)
        res = await self.session.execute(
            select(File).where(File.tenant_id == tenant_id).order_by(File.created_at.desc()).limit(limit).offset(offset)
        )
        return res.scalars().all()

    async def create(self, file: File) -> File:
        self.session.add(file)
        await self.session.commit()
        await self.session.refresh(file)
        return file


