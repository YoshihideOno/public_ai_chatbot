import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.repositories.base import BaseRepository
from app.repositories.chunks import ChunkRepository
from app.models.chunk import Chunk
from app.models import tenant as _tenant_model  # ensure FK targets loaded
from app.models import file as _file_model  # ensure FK targets loaded


pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_rls_isolation():
    async with AsyncSessionLocal() as db_session:
        repo = BaseRepository(db_session)
        tenant_a = str(uuid.uuid4())
        tenant_b = str(uuid.uuid4())

        # insert tenants directly with SQL to avoid defaults complexity
        await db_session.execute(
            text("INSERT INTO tenants(id, name, domain, api_key) VALUES (cast(:id as uuid), 'A', :domain, :api)"),
            {"id": tenant_a, "domain": f"a-{tenant_a}.example", "api": f"k-{tenant_a}"},
        )
        await db_session.execute(
            text("INSERT INTO tenants(id, name, domain, api_key) VALUES (cast(:id as uuid), 'B', :domain, :api)"),
            {"id": tenant_b, "domain": f"b-{tenant_b}.example", "api": f"k-{tenant_b}"},
        )
        await db_session.commit()

        # set tenant A and verify current setting
        await repo.set_tenant_context(tenant_a)
        rows = await repo.fetch_all("SELECT current_setting('app.tenant_id')")
        assert rows and rows[0][0] == tenant_a

        # switch to tenant B and verify current setting
        await repo.set_tenant_context(tenant_b)
        rows = await repo.fetch_all("SELECT current_setting('app.tenant_id')")
        assert rows and rows[0][0] == tenant_b


@pytest.mark.asyncio
async def test_trgm_search():
    async with AsyncSessionLocal() as db_session:
        tenant_id = str(uuid.uuid4())
        await db_session.execute(
            text("INSERT INTO tenants(id, name, domain, api_key) VALUES (cast(:id as uuid),'T', :domain, :api)"),
            {"id": tenant_id, "domain": f"t-{tenant_id}.example", "api": f"k-{tenant_id}"},
        )
        await db_session.commit()

        # seed a file and chunks
        file_id = str(uuid.uuid4())
        # create a user to satisfy files.uploaded_by FK
        user_id = str(uuid.uuid4())
        await db_session.execute(text("""
            INSERT INTO users(id, tenant_id, email, password_hash, name, role)
            VALUES (cast(:uid as uuid), cast(:tid as uuid), :email, :ph, 'tester', 'OPERATOR')
        """), {"uid": user_id, "tid": tenant_id, "email": f"t-{tenant_id}@example.com", "ph": "x"})
        await db_session.commit()
        await db_session.execute(text("""
            INSERT INTO files(id, tenant_id, file_name, file_type, size_bytes, status, s3_key, uploaded_by)
            VALUES (cast(:id as uuid), cast(:tid as uuid), 'faq.pdf', 'PDF', 100, 'UPLOADED', 's3://x', cast(:uid as uuid))
        """), {"id": file_id, "tid": tenant_id, "uid": user_id})
        await db_session.commit()
        await db_session.execute(text("""
            INSERT INTO chunks(id, file_id, tenant_id, chunk_index, chunk_text, metadata)
            VALUES
              (gen_random_uuid(), cast(:fid as uuid), cast(:tid as uuid), 0, '返品ポリシーについての説明です', '{}'::jsonb),
              (gen_random_uuid(), cast(:fid as uuid), cast(:tid as uuid), 1, '配送と返品の手順', '{}'::jsonb),
              (gen_random_uuid(), cast(:fid as uuid), cast(:tid as uuid), 2, '問い合わせ方法', '{}'::jsonb)
        """), {"fid": file_id, "tid": tenant_id})
        await db_session.commit()

        chunks_repo = ChunkRepository(db_session)
        matches = await chunks_repo.search_trgm(tenant_id, "返品", limit=5)
        assert len(matches) >= 1


@pytest.mark.asyncio
async def test_vector_search():
    async with AsyncSessionLocal() as db_session:
        tenant_id = str(uuid.uuid4())
        await db_session.execute(
            text("INSERT INTO tenants(id, name, domain, api_key) VALUES (cast(:id as uuid),'T', :domain, :api)"),
            {"id": tenant_id, "domain": f"t2-{tenant_id}.example", "api": f"k2-{tenant_id}"},
        )
        await db_session.commit()

        file_id = str(uuid.uuid4())
        # create a user to satisfy files.uploaded_by FK
        user_id = str(uuid.uuid4())
        await db_session.execute(text("""
            INSERT INTO users(id, tenant_id, email, password_hash, name, role)
            VALUES (cast(:uid as uuid), cast(:tid as uuid), :email, :ph, 'tester', 'OPERATOR')
        """), {"uid": user_id, "tid": tenant_id, "email": f"t2-{tenant_id}@example.com", "ph": "x"})
        await db_session.commit()
        await db_session.execute(text("""
            INSERT INTO files(id, tenant_id, file_name, file_type, size_bytes, status, s3_key, uploaded_by)
            VALUES (cast(:id as uuid), cast(:tid as uuid), 'kb.pdf', 'PDF', 10, 'UPLOADED', 's3://y', cast(:uid as uuid))
        """), {"id": file_id, "tid": tenant_id, "uid": user_id})
        await db_session.commit()
        # two embeddings (toy vectors, 1536-dim)
        v1 = [1.0] + [0.0] * 1535
        v2 = [0.9, 0.1] + [0.0] * 1534
        c1 = Chunk(
            id=uuid.uuid4(),
            file_id=uuid.UUID(file_id),
            tenant_id=uuid.UUID(tenant_id),
            chunk_index=0,
            chunk_text='A',
            metadata_json={},
            embedding=v1,
        )
        c2 = Chunk(
            id=uuid.uuid4(),
            file_id=uuid.UUID(file_id),
            tenant_id=uuid.UUID(tenant_id),
            chunk_index=1,
            chunk_text='B',
            metadata_json={},
            embedding=v2,
        )
        db_session.add_all([c1, c2])
        await db_session.commit()

        chunks_repo = ChunkRepository(db_session)
        # query vector close to [1,0,0,0]
        query_vec = [1.0] + [0.0] * 1535
        res = await chunks_repo.search_vector_l2(tenant_id, query_vec, limit=2)
        assert len(res) == 2
        # first one should be the closest
        assert res[0][1] <= res[1][1]


