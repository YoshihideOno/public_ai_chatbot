"""
pytest設定ファイル

このファイルはpytestのフィクスチャと共通設定を定義します。
テストで使用するデータベースセッション、テストクライアント、テストデータなどを提供します。
"""

import os
import sys
import uuid
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# テスト環境変数を設定（MissingGreenletエラーを回避するため）
os.environ["ENVIRONMENT"] = "test"
# ストレージは常に書き込み可能な /tmp 配下を使用
os.environ.setdefault("STORAGE_LOCAL_PATH", "/tmp/rag_pytest_storage")

# Ensure 'app' package is importable when running inside test container
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import get_password_hash
from main import app as fastapi_app


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """
    イベントループフィクスチャ（セッションスコープ）
    
    pytest-asyncioのデフォルトイベントループをセッションスコープにオーバーライドします。
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def db_session() -> AsyncSession:
    """
    データベースセッションフィクスチャ（セッションスコープ）
    
    テストで使用するデータベースセッションを提供します。
    テスト開始時にテーブルを作成します。
    """
    # テスト開始時にテーブルを作成
    from app.core.database import engine, Base
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client() -> TestClient:
    """
    テストクライアントフィクスチャ（セッションスコープ）
    
    FastAPIアプリケーションのテストクライアントを提供します。
    """
    with TestClient(fastapi_app) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def async_client() -> AsyncClient:
    """
    非同期テストクライアントフィクスチャ（セッションスコープ）
    
    FastAPIアプリケーションの非同期テストクライアントを提供します。
    バックグラウンドタスクを含む非同期処理のテストに使用します。
    """
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def tenant_id() -> str:
    """
    テナントIDフィクスチャ
    
    テストで使用する一意のテナントIDを生成します。
    """
    return str(uuid.uuid4())


@pytest_asyncio.fixture()
async def test_user(db_session: AsyncSession) -> User:
    """
    テスト用ユーザーフィクスチャ
    
    テストで使用するユーザーを作成します。
    テスト後に自動的にクリーンアップされます。
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"test-user-{unique_id}@example.com"
    username = f"testuser{unique_id}"
    password = "TestPassword1"
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=UserRole.OPERATOR,
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # クリーンアップ
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        await db_session.rollback()


@pytest_asyncio.fixture()
async def test_admin_user(db_session: AsyncSession) -> User:
    """
    テスト用管理者ユーザーフィクスチャ
    
    テストで使用する管理者ユーザーを作成します。
    テスト後に自動的にクリーンアップされます。
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"test-admin-{unique_id}@example.com"
    username = f"testadmin{unique_id}"
    password = "TestAdminPassword1"
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=UserRole.TENANT_ADMIN,
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # クリーンアップ
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        await db_session.rollback()


@pytest_asyncio.fixture()
async def test_platform_admin_user(db_session: AsyncSession) -> User:
    """
    テスト用プラットフォーム管理者ユーザーフィクスチャ
    
    テストで使用するプラットフォーム管理者ユーザーを作成します。
    テスト後に自動的にクリーンアップされます。
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"test-platform-admin-{unique_id}@example.com"
    username = f"testplatformadmin{unique_id}"
    password = "TestPlatformAdminPassword1"
    
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=UserRole.PLATFORM_ADMIN,
        is_active=True,
        is_verified=True,
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    yield user
    
    # クリーンアップ
    try:
        await db_session.delete(user)
        await db_session.commit()
    except Exception:
        await db_session.rollback()


@pytest_asyncio.fixture()
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """
    テスト用テナントフィクスチャ
    
    テストで使用するテナントを作成します。
    テスト後に自動的にクリーンアップされます。
    """
    from app.models.tenant import TenantStatus
    
    unique_id = str(uuid.uuid4())[:8]
    name = f"Test Tenant {unique_id}"
    domain = f"test-tenant-{unique_id}"
    
    tenant = Tenant(
        name=name,
        domain=domain,
        status=TenantStatus.ACTIVE,
    )
    
    db_session.add(tenant)
    await db_session.commit()
    await db_session.refresh(tenant)
    
    yield tenant
    
    # クリーンアップ
    try:
        await db_session.delete(tenant)
        await db_session.commit()
    except Exception:
        await db_session.rollback()


@pytest_asyncio.fixture()
async def authenticated_client(client: TestClient, db_session: AsyncSession) -> tuple[TestClient, str, User]:
    """
    認証済みクライアントフィクスチャ
    
    認証済みのテストクライアントとアクセストークン、ユーザーを提供します。
    """
    # 循環インポートを避けるため、ヘルパー関数を直接定義
    def register_user_and_tenant_helper(client: TestClient, email: str, password: str, tenant_name: str, tenant_domain: str, admin_username: str = None):
        if admin_username is None:
            admin_username_prefix = email.split('@')[0].replace('-', '_')
            admin_username_prefix = ''.join(c for c in admin_username_prefix if c.isalnum() or c == '_')
            admin_username = admin_username_prefix if len(admin_username_prefix) >= 3 else f"{admin_username_prefix}adm"
        response = client.post(
            f"{settings.API_V1_STR}/auth/register-tenant",
            json={
                "tenant_name": tenant_name,
                "tenant_domain": tenant_domain,
                "admin_email": email,
                "admin_username": admin_username,
                "admin_password": password
            }
        )
        return response
    
    def get_authenticated_client_helper(client: TestClient, email: str, password: str) -> tuple[TestClient, str]:
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        return client, access_token
    
    async def cleanup_test_data_helper(db_session: AsyncSession, email: str, tenant_domain: str):
        from app.models.tenant import Tenant
        try:
            user_result = await db_session.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if user:
                tenant_result = await db_session.execute(select(Tenant).where(Tenant.domain == tenant_domain))
                tenant = tenant_result.scalar_one_or_none()
                await db_session.delete(user)
                if tenant:
                    await db_session.delete(tenant)
                await db_session.commit()
        except Exception:
            await db_session.rollback()
            pass
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"auth-client-{unique_id}@example.com"
    password = "AuthClientPassword1"
    tenant_name = f"Auth Client Tenant {unique_id}"
    tenant_domain = f"auth-client-tenant-{unique_id}"
    
    try:
        register_user_and_tenant_helper(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client_helper(client, email, password)
        
        # ユーザーを取得
        user_result = await db_session.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()
        
        yield client, access_token, user
        
    finally:
        # クリーンアップ
        await cleanup_test_data_helper(db_session, email, tenant_domain)


# テストヘルパー関数
def create_test_user_data(role: UserRole = UserRole.OPERATOR) -> dict:
    """
    テスト用ユーザーデータを生成
    
    引数:
        role: ユーザーロール（デフォルト: OPERATOR）
    戻り値:
        dict: テスト用ユーザーデータ
    """
    unique_id = str(uuid.uuid4())[:8]
    return {
        "email": f"test-user-{unique_id}@example.com",
        "username": f"testuser{unique_id}",
        "password": "TestPassword1",
        "role": role
    }


def create_test_tenant_data() -> dict:
    """
    テスト用テナントデータを生成
    
    戻り値:
        dict: テスト用テナントデータ
    """
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": f"Test Tenant {unique_id}",
        "domain": f"test-tenant-{unique_id}"
    }

