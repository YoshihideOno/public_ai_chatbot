from __future__ import annotations

from typing import Sequence, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, bindparam, Integer
from app.models.chunk import Chunk
from .base import BaseRepository


class ChunkRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def list_by_file(self, tenant_id: str, file_id: str) -> Sequence[Chunk]:
        await self.set_tenant_context(tenant_id)
        res = await self.session.execute(select(Chunk).where(Chunk.file_id == file_id))
        return res.scalars().all()

    async def search_trgm(self, tenant_id: str, query: str, limit: int = 20) -> Sequence[tuple[str, float]]:
        """Trigram search using pg_trgm.
        Returns tuples of (chunk_id, similarity)
        """
        await self.set_tenant_context(tenant_id)
        sql = """
        SELECT id::text, similarity(chunk_text, :q) AS sim
        FROM chunks
        WHERE chunk_text ILIKE '%' || :q || '%'
        ORDER BY chunk_text <-> :q
        LIMIT :limit
        """
        rows = await self.fetch_all(sql, {"q": query, "limit": limit})
        return [(r[0], float(r[1])) for r in rows]

    async def search_vector_l2(self, tenant_id: str, embedding: list[float], limit: int = 20) -> Sequence[tuple[str, float]]:
        """Vector similarity search using L2 distance."""
        await self.set_tenant_context(tenant_id)
        stmt = text(
            """
            SELECT id::text, (embedding <-> :emb) AS dist
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> :emb
            LIMIT :limit
            """
        ).bindparams(
            bindparam("emb", type_=Chunk.embedding.type),
            bindparam("limit", type_=Integer),
        )
        res = await self.session.execute(stmt, {"emb": embedding, "limit": limit})
        rows = res.all()
        return [(r[0], float(r[1])) for r in rows]


