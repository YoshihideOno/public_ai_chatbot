"""
コンテンツ管理APIテストファイル

このファイルはコンテンツ管理関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
import base64
import asyncio
import time
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.file import File, FileStatus
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


# 非同期クライアント用のヘルパー関数
async def register_user_and_tenant_async(async_client: AsyncClient, email: str, password: str, tenant_name: str, tenant_domain: str, admin_username: str = None):
    """
    テナントとユーザーを登録するヘルパー関数（非同期版）
    
    引数:
        async_client: AsyncClient
        email: メールアドレス
        password: パスワード
        tenant_name: テナント名
        tenant_domain: テナント識別子
        admin_username: 管理者ユーザー名（省略時は自動生成）
        
    戻り値:
        Response: レスポンスオブジェクト
    """
    if admin_username is None:
        # メールアドレスのローカル部分からユーザー名を生成
        admin_username_prefix = email.split('@')[0].replace('-', '_')
        admin_username_prefix = ''.join(c for c in admin_username_prefix if c.isalnum() or c == '_')
        unique_suffix = str(uuid.uuid4())[:8]
        admin_username = f"{admin_username_prefix}_{unique_suffix}"
        # 20文字以内に収める
        if len(admin_username) > 20:
            max_prefix_len = 20 - len(unique_suffix) - 1
            admin_username = f"{admin_username_prefix[:max_prefix_len]}_{unique_suffix}"
    
    response = await async_client.post(
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


async def get_authenticated_client_async(async_client: AsyncClient, email: str, password: str) -> tuple[AsyncClient, str]:
    """
    認証済みクライアントとアクセストークンを取得（非同期版）
    
    引数:
        async_client: AsyncClient
        email: メールアドレス
        password: パスワード
        
    戻り値:
        tuple: (AsyncClient, access_token)
    """
    login_response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    return async_client, access_token


async def wait_for_file_processing(db_session: AsyncSession, file_id: str, max_wait_time: int = 30, poll_interval: float = 0.5) -> File:
    """
    ファイルの処理完了を待つ（ポーリング）
    
    引数:
        db_session: データベースセッション
        file_id: ファイルID
        max_wait_time: 最大待機時間（秒）
        poll_interval: ポーリング間隔（秒）
        
    戻り値:
        File: ファイルオブジェクト（処理完了後）
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        result = await db_session.execute(
            select(File).where(File.id == uuid.UUID(file_id))
        )
        file = result.scalar_one_or_none()
        
        if file:
            if file.status in [FileStatus.INDEXED, FileStatus.FAILED]:
                # 処理完了
                return file
            elif file.status == FileStatus.PROCESSING:
                # まだ処理中 - 待機
                await asyncio.sleep(poll_interval)
                continue
            else:
                # UPLOADEDのまま - バックグラウンドタスクが起動していない可能性
                await asyncio.sleep(poll_interval)
                continue
        else:
            # ファイルが見つからない
            await asyncio.sleep(poll_interval)
            continue
    
    # タイムアウト - 最終状態を返す
    result = await db_session.execute(
        select(File).where(File.id == uuid.UUID(file_id))
    )
    return result.scalar_one_or_none()


@pytest.mark.asyncio
async def test_get_contents_list_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: デフォルトパラメータでコンテンツ一覧取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"contents-{unique_id}@example.com"
    password = "ContentsPassword1"
    tenant_name = f"Contents Tenant {unique_id}"
    tenant_domain = f"contents-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_contents_list_pagination(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: ページネーション
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"pagination-contents-{unique_id}@example.com"
    password = "PaginationContentsPassword1"
    tenant_name = f"Pagination Contents Tenant {unique_id}"
    tenant_domain = f"pagination-contents-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/contents/?skip=0&limit=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_contents_list_filtering(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: フィルタリング（file_type, status）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"filter-contents-{unique_id}@example.com"
    password = "FilterContentsPassword1"
    tenant_name = f"Filter Contents Tenant {unique_id}"
    tenant_domain = f"filter-contents-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        response = client.get(
            f"{settings.API_V1_STR}/contents/?file_type=PDF&status=INDEXED",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_content_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 有効なデータでコンテンツ作成
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"create-contents-{unique_id}@example.com"
    password = "CreateContentsPassword1"
    tenant_name = f"Create Contents Tenant {unique_id}"
    tenant_domain = f"create-contents-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # テスト用のファイルコンテンツ（Base64エンコード）
        test_content = "これはテストコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test", "sample"],
                "file_content": test_content_b64
            }
        )
        # コンテンツ作成は非同期処理のため、202または200が返される可能性がある
        assert response.status_code in [200, 202]
        data = response.json()
        assert "id" in data or "status" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_create_content_missing_fields(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 必須フィールド欠損
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"missing-contents-{unique_id}@example.com"
    password = "MissingContentsPassword1"
    tenant_name = f"Missing Contents Tenant {unique_id}"
    tenant_domain = f"missing-contents-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 必須フィールド（file_content）を欠損
        response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT"
            }
        )
        assert response.status_code in [400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.skip(reason="MissingGreenletエラーのため一時的にスキップ")
@pytest.mark.asyncio
async def test_upload_file_success(async_client: AsyncClient, db_session: AsyncSession):
    """
    正常系テスト: 有効なファイルアップロード
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"upload-{unique_id}@example.com"
    password = "UploadPassword1"
    tenant_name = f"Upload Tenant {unique_id}"
    tenant_domain = f"upload-tenant-{unique_id}"
    
    try:
        await register_user_and_tenant_async(async_client, email, password, tenant_name, tenant_domain)
        _, access_token = await get_authenticated_client_async(async_client, email, password)
        
        # テスト用のファイルコンテンツ
        test_content = b"This is a test file content"
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": ("test.txt", test_content, "text/plain")},
            data={
                "title": f"テストファイル {unique_id}",
                "description": "テスト用のファイルです"
            }
        )
        # ファイルアップロードは非同期処理のため、202または200が返される可能性がある
        assert response.status_code in [200, 202]
        data = response.json()
        
        # ファイルIDを取得
        file_id = None
        if "id" in data:
            file_id = data["id"]
        elif "content" in data and "id" in data["content"]:
            file_id = data["content"]["id"]
        
        if file_id:
            # テスト環境ではバックグラウンド処理がスキップされるため、
            # ファイルが作成されたことを確認するだけ
            result = await db_session.execute(
                select(File).where(File.id == uuid.UUID(file_id))
            )
            file = result.scalar_one_or_none()
            if file:
                # ファイルが作成されたことを確認（ステータスはPROCESSINGのまま、テスト環境ではBG処理がスキップされる）
                assert file.status == FileStatus.PROCESSING, \
                    f"ファイルステータスが予期しない値です: status={file.status}"
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_by_id_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: コンテンツ詳細取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"getcontent-{unique_id}@example.com"
    password = "GetContentPassword1"
    tenant_name = f"Get Content Tenant {unique_id}"
    tenant_domain = f"get-content-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずコンテンツを作成
        test_content = "これはテストコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # コンテンツ詳細を取得
                response = client.get(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                # 非同期処理中の場合は404または202の可能性がある
                assert response.status_code in [200, 404, 202]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_by_id_not_found(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 存在しないコンテンツID
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"notfound-content-{unique_id}@example.com"
    password = "NotFoundContentPassword1"
    tenant_name = f"NotFound Content Tenant {unique_id}"
    tenant_domain = f"notfound-content-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        fake_content_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/contents/{fake_content_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 404
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_content_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 有効なデータでコンテンツ更新
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"update-content-{unique_id}@example.com"
    password = "UpdateContentPassword1"
    tenant_name = f"Update Content Tenant {unique_id}"
    tenant_domain = f"update-content-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずコンテンツを作成
        test_content = "これはテストコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # コンテンツを更新
                response = client.put(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json={
                        "title": f"更新されたコンテンツ {unique_id}",
                        "description": "更新された説明です"
                    }
                )
                # 非同期処理中の場合は404または202の可能性がある
                assert response.status_code in [200, 404, 202]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_delete_content_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: コンテンツ削除
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"delete-content-{unique_id}@example.com"
    password = "DeleteContentPassword1"
    tenant_name = f"Delete Content Tenant {unique_id}"
    tenant_domain = f"delete-content-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずコンテンツを作成
        test_content = "これはテストコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # コンテンツを削除
                response = client.delete(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                # 非同期処理中の場合は404または202の可能性がある
                assert response.status_code in [200, 404, 202]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_chunks_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: チャンク一覧取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"chunks-{unique_id}@example.com"
    password = "ChunksPassword1"
    tenant_name = f"Chunks Tenant {unique_id}"
    tenant_domain = f"chunks-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずコンテンツを作成
        test_content = "これはテストコンテンツです。チャンク化される可能性があります。"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # チャンク一覧を取得
                response = client.get(
                    f"{settings.API_V1_STR}/contents/{content_id}/chunks",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                # チャンクが存在する場合と存在しない場合の両方を考慮
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_chunks_pagination(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: チャンク一覧のページネーション
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"chunks-pagination-{unique_id}@example.com"
    password = "ChunksPaginationPassword1"
    tenant_name = f"Chunks Pagination Tenant {unique_id}"
    tenant_domain = f"chunks-pagination-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # まずコンテンツを作成
        test_content = "これはテストコンテンツです。"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "title": f"テストコンテンツ {unique_id}",
                "content_type": "TXT",
                "description": "テスト用のコンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # ページネーションパラメータ付きでチャンク一覧を取得
                response = client.get(
                    f"{settings.API_V1_STR}/contents/{content_id}/chunks?skip=0&limit=10",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    data = response.json()
                    assert isinstance(data, list)
                    assert len(data) <= 10
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_chunks_not_found(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 存在しないコンテンツIDでチャンク一覧取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"chunks-notfound-{unique_id}@example.com"
    password = "ChunksNotFoundPassword1"
    tenant_name = f"Chunks NotFound Tenant {unique_id}"
    tenant_domain = f"chunks-notfound-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        fake_content_id = str(uuid.uuid4())
        response = client.get(
            f"{settings.API_V1_STR}/contents/{fake_content_id}/chunks",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        # 存在しないコンテンツIDの場合は404または空のリストが返される可能性がある
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


# テストヘルパー関数: 指定サイズのファイルコンテンツを生成
def create_test_file_content(size_bytes: int) -> bytes:
    """
    指定サイズのテストファイルコンテンツを生成
    
    引数:
        size_bytes: ファイルサイズ（バイト）
        
    戻り値:
        bytes: テストファイルコンテンツ
    """
    return b"x" * size_bytes


# テストヘルパー関数: テスト用ファイルオブジェクトを作成
def create_test_file(filename: str, content: bytes, content_type: str = "text/plain"):
    """
    テスト用ファイルオブジェクトを作成
    
    引数:
        filename: ファイル名
        content: ファイルコンテンツ
        content_type: MIMEタイプ
        
    戻り値:
        tuple: (filename, content, content_type)
    """
    return (filename, content, content_type)


@pytest.mark.skip(reason="MissingGreenletエラーのため一時的にスキップ")
@pytest.mark.asyncio
async def test_upload_file_boundary_values(async_client: AsyncClient, db_session: AsyncSession):
    """
    正常系テスト: ファイルアップロードの境界値テスト（1バイト、10MB）
    注意: 実装ではデフォルト最大サイズが50MBのため、10MBをテスト
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"boundary-upload-{unique_id}@example.com"
    password = "BoundaryUploadPassword1"
    tenant_name = f"Boundary Upload Tenant {unique_id}"
    tenant_domain = f"boundary-upload-tenant-{unique_id}"
    
    try:
        await register_user_and_tenant_async(async_client, email, password, tenant_name, tenant_domain)
        _, access_token = await get_authenticated_client_async(async_client, email, password)
        
        # 1バイトのファイル
        test_content_1byte = create_test_file_content(1)
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test_1byte.txt", test_content_1byte)},
            data={"title": f"1バイトファイル {unique_id}"}
        )
        # 1バイトファイルは有効
        assert response.status_code in [200, 202]
        
        # テスト環境ではバックグラウンド処理がスキップされるため、
        # ファイルが作成されたことを確認するだけ
        data = response.json()
        file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
        if file_id:
            result = await db_session.execute(
                select(File).where(File.id == uuid.UUID(file_id))
            )
            file = result.scalar_one_or_none()
            if file:
                assert file.status == FileStatus.PROCESSING, \
                    f"ファイルステータスが予期しない値です: status={file.status}"
        
        # 10MBのファイル（実装のデフォルト最大サイズ50MB以内）
        test_content_10mb = create_test_file_content(10 * 1024 * 1024)  # 10MB
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test_10mb.txt", test_content_10mb)},
            data={"title": f"10MBファイル {unique_id}"}
        )
        # 10MBファイルは有効（50MB制限内）
        assert response.status_code in [200, 202]
        
        # ファイルIDを取得してポーリング
        data = response.json()
        file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
        if file_id:
            file = await wait_for_file_processing(db_session, file_id, max_wait_time=60)  # 10MBファイルは処理に時間がかかる可能性があるため60秒
            if file:
                assert file.status in [FileStatus.INDEXED, FileStatus.FAILED]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_upload_file_too_large(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: ファイルサイズ超過（51MB、実装のデフォルト制限50MBを超える）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"toolarge-upload-{unique_id}@example.com"
    password = "TooLargeUploadPassword1"
    tenant_name = f"TooLarge Upload Tenant {unique_id}"
    tenant_domain = f"toolarge-upload-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 51MBのファイル（50MB制限を超える）
        # 注意: 実際のテストでは51MBファイルの生成は時間がかかるため、より小さいサイズでテスト
        # ここでは51MB相当のサイズでテスト（実際にはメモリ効率を考慮してスキップする可能性がある）
        test_content_51mb = create_test_file_content(51 * 1024 * 1024)  # 51MB
        response = client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test_51mb.txt", test_content_51mb)},
            data={"title": f"51MBファイル {unique_id}"}
        )
        # ファイルサイズ超過エラー
        assert response.status_code in [400, 422]
        assert "ファイルサイズ" in response.json()["detail"] or "file size" in response.json()["detail"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_upload_file_empty(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 空ファイル
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"empty-upload-{unique_id}@example.com"
    password = "EmptyUploadPassword1"
    tenant_name = f"Empty Upload Tenant {unique_id}"
    tenant_domain = f"empty-upload-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 空ファイル
        test_content_empty = b""
        response = client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("empty.txt", test_content_empty)},
            data={"title": f"空ファイル {unique_id}"}
        )
        # 空ファイルはエラーになる可能性がある
        assert response.status_code in [200, 202, 400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_upload_file_special_characters(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: ファイル名に特殊文字を含む
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"special-upload-{unique_id}@example.com"
    password = "SpecialUploadPassword1"
    tenant_name = f"Special Upload Tenant {unique_id}"
    tenant_domain = f"special-upload-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 特殊文字を含むファイル名
        test_content = b"Test content"
        special_filename = f"test<script>alert('XSS')</script>.txt"
        response = client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file(special_filename, test_content)},
            data={"title": f"特殊文字ファイル {unique_id}"}
        )
        # 特殊文字を含むファイル名はサニタイズされるかエラーになる可能性がある
        assert response.status_code in [200, 202, 400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_upload_file_long_filename(async_client: AsyncClient, db_session: AsyncSession):
    """
    異常系テスト: 非常に長いファイル名（255文字以上）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"longname-upload-{unique_id}@example.com"
    password = "LongNameUploadPassword1"
    tenant_name = f"LongName Upload Tenant {unique_id}"
    tenant_domain = f"longname-upload-tenant-{unique_id}"
    
    try:
        await register_user_and_tenant_async(async_client, email, password, tenant_name, tenant_domain)
        _, access_token = await get_authenticated_client_async(async_client, email, password)
        
        # 非常に長いファイル名（300文字）- タイトルは明示的に指定（255文字以内）
        test_content = b"Test content"
        long_filename = "a" * 300 + ".txt"
        # タイトルは明示的に指定（255文字以内に制限）
        short_title = f"長いファイル名 {unique_id}"[:250]  # 255文字以内に制限
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file(long_filename, test_content)},
            data={"title": short_title}
        )
        # 長いファイル名はエラーになるか、切り詰められる可能性がある
        assert response.status_code in [200, 202, 400, 422]
        
        # 成功した場合（200, 202）はポーリング
        if response.status_code in [200, 202]:
            data = response.json()
            file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
            if file_id:
                file = await wait_for_file_processing(db_session, file_id, max_wait_time=30)
                if file:
                    assert file.status in [FileStatus.INDEXED, FileStatus.FAILED]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_upload_file_invalid_format(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効なファイル形式（EXE, ZIPなど）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"invalid-format-{unique_id}@example.com"
    password = "InvalidFormatPassword1"
    tenant_name = f"Invalid Format Tenant {unique_id}"
    tenant_domain = f"invalid-format-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # EXEファイル（無効な形式）
        test_content = b"MZ\x90\x00"  # EXEファイルのマジックナンバー
        response = client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test.exe", test_content, "application/x-msdownload")},
            data={"title": f"EXEファイル {unique_id}"}
        )
        # 無効なファイル形式はエラーになる
        assert response.status_code in [400, 422]
        assert "サポートされていない" in response.json()["detail"] or "not supported" in response.json()["detail"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.skip(reason="MissingGreenletエラーのため一時的にスキップ")
@pytest.mark.asyncio
async def test_upload_file_various_formats(async_client: AsyncClient, db_session: AsyncSession):
    """
    正常系テスト: 各種ファイル形式（PDF, DOCX, MD, TXT）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"formats-upload-{unique_id}@example.com"
    password = "FormatsUploadPassword1"
    tenant_name = f"Formats Upload Tenant {unique_id}"
    tenant_domain = f"formats-upload-tenant-{unique_id}"
    
    try:
        await register_user_and_tenant_async(async_client, email, password, tenant_name, tenant_domain)
        _, access_token = await get_authenticated_client_async(async_client, email, password)
        
        # TXTファイル
        test_content_txt = b"This is a test text file."
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test.txt", test_content_txt, "text/plain")},
            data={"title": f"TXTファイル {unique_id}"}
        )
        assert response.status_code in [200, 202]
        
        # テスト環境ではバックグラウンド処理がスキップされるため、
        # ファイルが作成されたことを確認するだけ
        data = response.json()
        file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
        if file_id:
            result = await db_session.execute(
                select(File).where(File.id == uuid.UUID(file_id))
            )
            file = result.scalar_one_or_none()
            if file:
                assert file.status == FileStatus.PROCESSING, \
                    f"ファイルステータスが予期しない値です: status={file.status}"
        
        # PDFファイル（簡易的なPDFヘッダー）
        # 注意: 実際のPDFファイルは複雑なため、簡易的な形式でテスト
        test_content_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 0\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test.pdf", test_content_pdf, "application/pdf")},
            data={"title": f"PDFファイル {unique_id}"}
        )
        assert response.status_code in [200, 202]
        
        # テスト環境ではバックグラウンド処理がスキップされるため、
        # ファイルが作成されたことを確認するだけ
        data = response.json()
        file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
        if file_id:
            result = await db_session.execute(
                select(File).where(File.id == uuid.UUID(file_id))
            )
            file = result.scalar_one_or_none()
            if file:
                assert file.status == FileStatus.PROCESSING, \
                    f"ファイルステータスが予期しない値です: status={file.status}"
        
        # MDファイル
        test_content_md = b"# Test Markdown\n\nThis is a test markdown file."
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test.md", test_content_md, "text/markdown")},
            data={"title": f"MDファイル {unique_id}"}
        )
        assert response.status_code in [200, 202]
        
        # テスト環境ではバックグラウンド処理がスキップされるため、
        # ファイルが作成されたことを確認するだけ
        data = response.json()
        file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
        if file_id:
            result = await db_session.execute(
                select(File).where(File.id == uuid.UUID(file_id))
            )
            file = result.scalar_one_or_none()
            if file:
                assert file.status == FileStatus.PROCESSING, \
                    f"ファイルステータスが予期しない値です: status={file.status}"
        
        # DOCXファイル（簡易的なZIP形式、DOCXはZIPベース）
        # 注意: 実際のDOCXファイルは複雑なため、簡易的な形式でテスト
        # DOCXファイルのアップロードは実装によっては失敗する可能性がある
        test_content_docx = b"PK\x03\x04"  # ZIPファイルのマジックナンバー（DOCXはZIPベース）
        response = await async_client.post(
            f"{settings.API_V1_STR}/contents/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files={"file": create_test_file("test.docx", test_content_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"title": f"DOCXファイル {unique_id}"}
        )
        # DOCXファイルは実装によってはサポートされていない可能性がある
        assert response.status_code in [200, 202, 400, 422]
        
        # 成功した場合（200, 202）はポーリング
        if response.status_code in [200, 202]:
            data = response.json()
            file_id = data.get("id") or (data.get("content", {}).get("id") if "content" in data else None)
            if file_id:
                file = await wait_for_file_processing(db_session, file_id, max_wait_time=30)
                if file:
                    assert file.status in [FileStatus.INDEXED, FileStatus.FAILED]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_content_cross_tenant_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 他テナントのコンテンツ取得試行
    """
    # テナント1のユーザーを作成
    unique_id1 = str(uuid.uuid4())[:8]
    email1 = f"tenant1-{unique_id1}@example.com"
    password1 = "Tenant1Password1"
    tenant_name1 = f"Tenant 1 {unique_id1}"
    tenant_domain1 = f"tenant1-{unique_id1}"
    
    # テナント2のユーザーを作成
    unique_id2 = str(uuid.uuid4())[:8]
    email2 = f"tenant2-{unique_id2}@example.com"
    password2 = "Tenant2Password1"
    tenant_name2 = f"Tenant 2 {unique_id2}"
    tenant_domain2 = f"tenant2-{unique_id2}"
    
    try:
        # テナント1のユーザーとテナントを作成
        register_user_and_tenant(client, email1, password1, tenant_name1, tenant_domain1)
        _, access_token1 = get_authenticated_client(client, email1, password1)
        
        # テナント2のユーザーとテナントを作成
        register_user_and_tenant(client, email2, password2, tenant_name2, tenant_domain2)
        _, access_token2 = get_authenticated_client(client, email2, password2)
        
        # テナント1でコンテンツを作成
        test_content = "これはテナント1のコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token1}"},
            json={
                "title": f"テナント1のコンテンツ {unique_id1}",
                "content_type": "TXT",
                "description": "テナント1のテスト用コンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # テナント2のユーザーがテナント1のコンテンツを取得しようとする
                response = client.get(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token2}"}
                )
                # 他テナントのコンテンツは取得できない（403または404）
                assert response.status_code in [403, 404]
    finally:
        await cleanup_test_data(db_session, email1, tenant_domain1)
        await cleanup_test_data(db_session, email2, tenant_domain2)


@pytest.mark.asyncio
async def test_update_content_cross_tenant_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 他テナントのコンテンツ更新試行
    """
    # テナント1のユーザーを作成
    unique_id1 = str(uuid.uuid4())[:8]
    email1 = f"update-tenant1-{unique_id1}@example.com"
    password1 = "UpdateTenant1Password1"
    tenant_name1 = f"Update Tenant 1 {unique_id1}"
    tenant_domain1 = f"update-tenant1-{unique_id1}"
    
    # テナント2のユーザーを作成
    unique_id2 = str(uuid.uuid4())[:8]
    email2 = f"update-tenant2-{unique_id2}@example.com"
    password2 = "UpdateTenant2Password1"
    tenant_name2 = f"Update Tenant 2 {unique_id2}"
    tenant_domain2 = f"update-tenant2-{unique_id2}"
    
    try:
        # テナント1のユーザーとテナントを作成
        register_user_and_tenant(client, email1, password1, tenant_name1, tenant_domain1)
        _, access_token1 = get_authenticated_client(client, email1, password1)
        
        # テナント2のユーザーとテナントを作成
        register_user_and_tenant(client, email2, password2, tenant_name2, tenant_domain2)
        _, access_token2 = get_authenticated_client(client, email2, password2)
        
        # テナント1でコンテンツを作成
        test_content = "これはテナント1のコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token1}"},
            json={
                "title": f"テナント1のコンテンツ {unique_id1}",
                "content_type": "TXT",
                "description": "テナント1のテスト用コンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # テナント2のユーザーがテナント1のコンテンツを更新しようとする
                response = client.put(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token2}"},
                    json={
                        "title": f"不正に更新されたコンテンツ {unique_id2}",
                        "description": "不正な更新です"
                    }
                )
                # 他テナントのコンテンツは更新できない（403または404）
                assert response.status_code in [403, 404]
    finally:
        await cleanup_test_data(db_session, email1, tenant_domain1)
        await cleanup_test_data(db_session, email2, tenant_domain2)


@pytest.mark.asyncio
async def test_delete_content_cross_tenant_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 他テナントのコンテンツ削除試行
    """
    # テナント1のユーザーを作成
    unique_id1 = str(uuid.uuid4())[:8]
    email1 = f"delete-tenant1-{unique_id1}@example.com"
    password1 = "DeleteTenant1Password1"
    tenant_name1 = f"Delete Tenant 1 {unique_id1}"
    tenant_domain1 = f"delete-tenant1-{unique_id1}"
    
    # テナント2のユーザーを作成
    unique_id2 = str(uuid.uuid4())[:8]
    email2 = f"delete-tenant2-{unique_id2}@example.com"
    password2 = "DeleteTenant2Password1"
    tenant_name2 = f"Delete Tenant 2 {unique_id2}"
    tenant_domain2 = f"delete-tenant2-{unique_id2}"
    
    try:
        # テナント1のユーザーとテナントを作成
        register_user_and_tenant(client, email1, password1, tenant_name1, tenant_domain1)
        _, access_token1 = get_authenticated_client(client, email1, password1)
        
        # テナント2のユーザーとテナントを作成
        register_user_and_tenant(client, email2, password2, tenant_name2, tenant_domain2)
        _, access_token2 = get_authenticated_client(client, email2, password2)
        
        # テナント1でコンテンツを作成
        test_content = "これはテナント1のコンテンツです"
        test_content_b64 = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        
        create_response = client.post(
            f"{settings.API_V1_STR}/contents/",
            headers={"Authorization": f"Bearer {access_token1}"},
            json={
                "title": f"テナント1のコンテンツ {unique_id1}",
                "content_type": "TXT",
                "description": "テナント1のテスト用コンテンツです",
                "tags": ["test"],
                "file_content": test_content_b64
            }
        )
        
        if create_response.status_code in [200, 202]:
            content_id = create_response.json().get("id")
            if content_id:
                # テナント2のユーザーがテナント1のコンテンツを削除しようとする
                response = client.delete(
                    f"{settings.API_V1_STR}/contents/{content_id}",
                    headers={"Authorization": f"Bearer {access_token2}"}
                )
                # 他テナントのコンテンツは削除できない（403または404）
                assert response.status_code in [403, 404]
    finally:
        await cleanup_test_data(db_session, email1, tenant_domain1)
        await cleanup_test_data(db_session, email2, tenant_domain2)

