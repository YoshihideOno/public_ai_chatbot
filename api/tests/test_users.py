"""
ユーザー管理APIテストファイル

このファイルはユーザー管理関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import verify_password
# テストヘルパー関数をインポート
# 注意: test_auth.pyからインポートする代わりに、conftest.pyに移動することを検討
try:
    from tests.test_auth import register_user_and_tenant, cleanup_test_data, register_user, cleanup_user, get_authenticated_client
except ImportError:
    # 循環インポートを避けるため、直接定義
    def register_user_and_tenant(client: TestClient, email: str, password: str, tenant_name: str, tenant_domain: str, admin_username: str = None):
        from app.core.config import settings
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
    
    async def cleanup_test_data(db_session: AsyncSession, email: str, tenant_domain: str):
        from sqlalchemy import select
        from app.models.user import User
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
    
    def register_user(client: TestClient, email: str, password: str, username: str, role: str = "OPERATOR"):
        from app.core.config import settings
        response = client.post(
            f"{settings.API_V1_STR}/auth/register",
            json={
                "email": email,
                "username": username,
                "password": password,
                "role": role
            }
        )
        return response
    
    async def cleanup_user(db_session: AsyncSession, email: str):
        from sqlalchemy import select
        from app.models.user import User
        try:
            user_result = await db_session.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if user:
                await db_session.delete(user)
                await db_session.commit()
        except Exception:
            await db_session.rollback()
            pass
    
    def get_authenticated_client(client: TestClient, email: str, password: str) -> tuple[TestClient, str]:
        """
        認証済みクライアントとアクセストークンを取得
        
        引数:
            client: TestClient
            email: メールアドレス
            password: パスワード
            
        戻り値:
            tuple: (TestClient, access_token)
        """
        from app.core.config import settings
        login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]
        return client, access_token


@pytest.mark.asyncio
async def test_get_current_user_info_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 有効なトークンで現在のユーザー情報取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"current-{unique_id}@example.com"
    password = "CurrentUserPassword1"
    tenant_name = f"Current User Tenant {unique_id}"
    tenant_domain = f"current-user-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "id" in data
        assert "username" in data
        assert "role" in data
        assert "tenant_id" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_current_user_info_invalid_token(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効なトークンでユーザー情報取得
    """
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    # HTTPBearerはトークンがない場合に403を返す可能性がある
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_current_user_info_no_token(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: トークンなしでユーザー情報取得
    """
    response = client.get(
        f"{settings.API_V1_STR}/users/me"
    )
    # HTTPBearerはトークンがない場合に403を返す可能性がある
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_update_current_user_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 有効なデータで現在のユーザー情報更新
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"update-{unique_id}@example.com"
    password = "UpdateUserPassword1"
    tenant_name = f"Update User Tenant {unique_id}"
    tenant_domain = f"update-user-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        new_username = f"updateduser{unique_id}"
        response = client.put(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"username": new_username}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == new_username
        assert data["email"] == email  # メールアドレスは変更されていない
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_current_user_role_change_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: ロール変更試行（拒否されるべき）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"rolechange-{unique_id}@example.com"
    password = "RoleChangePassword1"
    tenant_name = f"Role Change Tenant {unique_id}"
    tenant_domain = f"role-change-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.put(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"role": "TENANT_ADMIN"}
        )
        assert response.status_code == 403
        assert "Cannot change your own role" in response.json()["detail"] or "ロールを変更できません" in response.json()["detail"]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_users_list_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: デフォルトパラメータでユーザー一覧取得（管理者）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"admin-{unique_id}@example.com"
    password = "AdminPassword1"
    tenant_name = f"Admin Tenant {unique_id}"
    tenant_domain = f"admin-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # 少なくとも登録したユーザーが含まれている
        assert any(user["email"] == email for user in data)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_users_list_pagination(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: ページネーション（skip, limit）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"pagination-{unique_id}@example.com"
    password = "PaginationPassword1"
    tenant_name = f"Pagination Tenant {unique_id}"
    tenant_domain = f"pagination-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/users/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_user_by_id_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 自分のユーザー情報取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"getuser-{unique_id}@example.com"
    password = "GetUserPassword1"
    tenant_name = f"Get User Tenant {unique_id}"
    tenant_domain = f"get-user-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まず自分の情報を取得
        me_response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        user_id = me_response.json()["id"]
        
        # ユーザーIDで取得
        response = client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == email
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 存在しないユーザーID
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"notfound-{unique_id}@example.com"
    password = "NotFoundPassword1"
    tenant_name = f"NotFound Tenant {unique_id}"
    tenant_domain = f"notfound-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        fake_user_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/users/{fake_user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 404
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_user_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 管理者がユーザー作成
    """
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"admin-create-{unique_id}@example.com"
    password = "AdminCreatePassword1"
    tenant_name = f"Admin Create Tenant {unique_id}"
    tenant_domain = f"admin-create-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, admin_email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, admin_email, password)
        
        new_user_email = f"newuser-{unique_id}@example.com"
        new_username = f"newuser{unique_id}"
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "email": new_user_email,
                "username": new_username,
                "password": "NewUserPassword1",
                "role": "OPERATOR"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_user_email
        assert data["username"] == new_username
        
        # データベースで確認
        user_result = await db_session.execute(select(User).where(User.email == new_user_email))
        user = user_result.scalar_one_or_none()
        assert user is not None
        assert user.email == new_user_email
    finally:
        await cleanup_test_data(db_session, admin_email, tenant_domain)
        # 作成したユーザーもクリーンアップ
        try:
            await cleanup_user(db_session, f"newuser-{unique_id}@example.com")
        except:
            pass


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 既存メールアドレスでユーザー作成
    """
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"admin-dup-{unique_id}@example.com"
    password = "AdminDupPassword1"
    tenant_name = f"Admin Dup Tenant {unique_id}"
    tenant_domain = f"admin-dup-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, admin_email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, admin_email, password)
        
        # 既存のメールアドレスでユーザー作成を試みる
        response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "email": admin_email,
                "username": f"duplicate{unique_id}",
                "password": "DuplicatePassword1",
                "role": "OPERATOR"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"] or "メールアドレスは既に登録されています" in response.json()["detail"]
    finally:
        await cleanup_test_data(db_session, admin_email, tenant_domain)


@pytest.mark.asyncio
async def test_update_user_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 管理者がユーザー情報更新
    """
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"admin-update-{unique_id}@example.com"
    password = "AdminUpdatePassword1"
    tenant_name = f"Admin Update Tenant {unique_id}"
    tenant_domain = f"admin-update-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, admin_email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, admin_email, password)
        
        # 新しいユーザーを作成
        new_user_email = f"toupdate-{unique_id}@example.com"
        new_username = f"toupdate{unique_id}"
        create_response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "email": new_user_email,
                "username": new_username,
                "password": "ToUpdatePassword1",
                "role": "OPERATOR"
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # ユーザー情報を更新
        updated_username = f"updated{unique_id}"
        response = client.put(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"username": updated_username}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == updated_username
    finally:
        await cleanup_test_data(db_session, admin_email, tenant_domain)
        try:
            await cleanup_user(db_session, f"toupdate-{unique_id}@example.com")
        except:
            pass


@pytest.mark.asyncio
async def test_delete_user_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 管理者がユーザー削除
    """
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"admin-delete-{unique_id}@example.com"
    password = "AdminDeletePassword1"
    tenant_name = f"Admin Delete Tenant {unique_id}"
    tenant_domain = f"admin-delete-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, admin_email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, admin_email, password)
        
        # 新しいユーザーを作成
        new_user_email = f"todelete-{unique_id}@example.com"
        new_username = f"todelete{unique_id}"
        create_response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "email": new_user_email,
                "username": new_username,
                "password": "ToDeletePassword1",
                "role": "OPERATOR"
            }
        )
        assert create_response.status_code == 200
        user_id = create_response.json()["id"]
        
        # ユーザーを削除
        response = client.delete(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower() or "削除" in response.json()["message"]
        
        # 削除されたユーザーは取得できないことを確認
        get_response = client.get(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # ソフトデリートの場合は404、ハードデリートの場合は404
        assert get_response.status_code == 404
    finally:
        await cleanup_test_data(db_session, admin_email, tenant_domain)
        try:
            await cleanup_user(db_session, f"todelete-{unique_id}@example.com")
        except:
            pass


@pytest.mark.asyncio
async def test_delete_user_self_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 自分自身の削除試行
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"selfdelete-{unique_id}@example.com"
    password = "SelfDeletePassword1"
    tenant_name = f"Self Delete Tenant {unique_id}"
    tenant_domain = f"self-delete-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 自分のIDを取得
        me_response = client.get(
            f"{settings.API_V1_STR}/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        user_id = me_response.json()["id"]
        
        # 自分自身を削除しようとする
        response = client.delete(
            f"{settings.API_V1_STR}/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"] or "自分のアカウントを削除できません" in response.json()["detail"]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_export_users_filtering(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: エクスポート機能のフィルタリング（role, is_active）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"export-filter-{unique_id}@example.com"
    password = "ExportFilterPassword1"
    tenant_name = f"Export Filter Tenant {unique_id}"
    tenant_domain = f"export-filter-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # roleでフィルタリング
        response = client.get(
            f"{settings.API_V1_STR}/users/actions/export?format=csv&role=TENANT_ADMIN",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] in ["text/csv; charset=utf-8", "application/json; charset=utf-8"]
        
        # is_activeでフィルタリング
        response = client.get(
            f"{settings.API_V1_STR}/users/actions/export?format=csv&is_active=true",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        
        # roleとis_activeの組み合わせ
        response = client.get(
            f"{settings.API_V1_STR}/users/actions/export?format=csv&role=OPERATOR&is_active=true",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_export_users_search(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: エクスポート機能の検索（search）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"export-search-{unique_id}@example.com"
    password = "ExportSearchPassword1"
    tenant_name = f"Export Search Tenant {unique_id}"
    tenant_domain = f"export-search-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 検索パラメータ付きでエクスポート
        response = client.get(
            f"{settings.API_V1_STR}/users/actions/export?format=csv&search={unique_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] in ["text/csv; charset=utf-8", "application/json; charset=utf-8"]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_export_users_json_format(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: エクスポート機能のJSON形式
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"export-json-{unique_id}@example.com"
    password = "ExportJsonPassword1"
    tenant_name = f"Export JSON Tenant {unique_id}"
    tenant_domain = f"export-json-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # JSON形式でエクスポート
        response = client.get(
            f"{settings.API_V1_STR}/users/actions/export?format=json",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_users_list_operator_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: OPERATORが全ユーザー取得を試行した場合の権限エラー
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"operator-{unique_id}@example.com"
    password = "OperatorPassword1"
    tenant_name = f"Operator Tenant {unique_id}"
    tenant_domain = f"operator-tenant-{unique_id}"
    
    try:
        # テナント管理者として登録
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, admin_token = get_authenticated_client(client, email, password)
        
        # OPERATORロールのユーザーを作成
        operator_email = f"operator-user-{unique_id}@example.com"
        operator_username = f"operatoruser{unique_id}"
        create_user_response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": operator_email,
                "username": operator_username,
                "password": "OperatorUserPassword1",
                "role": "OPERATOR"
            }
        )
        assert create_user_response.status_code in [200, 201]
        
        # OPERATORユーザーでログイン
        operator_login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": operator_email, "password": "OperatorUserPassword1"}
        )
        assert operator_login_response.status_code == 200
        operator_token = operator_login_response.json()["access_token"]
        
        # OPERATORが全ユーザー取得を試行
        response = client.get(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        # OPERATORは全ユーザー取得できない（403エラー）
        assert response.status_code == 403
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)

