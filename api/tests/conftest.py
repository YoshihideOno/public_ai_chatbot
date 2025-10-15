import os
import sys
import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Ensure 'app' package is importable when running inside test container
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.core.database import AsyncSessionLocal


@pytest_asyncio.fixture(scope="session")
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture()
def tenant_id() -> str:
    return str(uuid.uuid4())


