from __future__ import annotations

from typing import Any, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_tenant_context(self, tenant_id: str) -> None:
        """Set current tenant id for RLS policies.

        NOTE: Call this at the beginning of a request/operation that relies on RLS.
        """
        await self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, false)").bindparams(tenant_id=tenant_id)
        )

    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        await self.session.execute(text(sql), params or {})

    async def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> Sequence[Any]:
        result = await self.session.execute(text(sql), params or {})
        return result.fetchall()


