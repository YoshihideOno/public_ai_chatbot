"""
クエリアナリティクスAPIテストファイル

このファイルはクエリアナリティクス関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock
from app.core.config import settings
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
@patch('app.services.query_analytics_service.QueryAnalyticsService.rebuild', new_callable=AsyncMock)
async def test_rebuild_query_analytics_success(mock_rebuild: AsyncMock, client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: クエリアナリティクスの再集計実行（TENANT_ADMIN以上）
    """
    mock_rebuild.return_value = None
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"rebuild-analytics-{unique_id}@example.com"
    password = "RebuildAnalyticsPassword1"
    tenant_name = f"Rebuild Analytics Tenant {unique_id}"
    tenant_domain = f"rebuild-analytics-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 再集計実行
        response = client.post(
            f"{settings.API_V1_STR}/query-analytics/rebuild",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "month",
                "top_k": 10
            }
        )
        assert response.status_code == 200
        assert "message" in response.json()
        mock_rebuild.assert_called_once()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_rebuild_query_analytics_operator_forbidden(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: OPERATORが再集計実行を試行（403エラー）
    """
    # テナント管理者として登録
    unique_id = str(uuid.uuid4())[:8]
    admin_email = f"admin-analytics-{unique_id}@example.com"
    password = "AdminAnalyticsPassword1"
    tenant_name = f"Admin Analytics Tenant {unique_id}"
    tenant_domain = f"admin-analytics-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, admin_email, password, tenant_name, tenant_domain)
        _, admin_token = get_authenticated_client(client, admin_email, password)
        
        # OPERATORロールのユーザーを作成
        from tests.test_auth import register_user, cleanup_user
        operator_email = f"operator-analytics-{unique_id}@example.com"
        operator_username = f"opanalytics{unique_id}"  # 20文字以内に収める
        create_user_response = client.post(
            f"{settings.API_V1_STR}/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": operator_email,
                "username": operator_username,
                "password": "OperatorAnalyticsPassword1",
                "role": "OPERATOR"
            }
        )
        assert create_user_response.status_code in [200, 201]
        
        # OPERATORユーザーでログイン
        operator_login_response = client.post(
            f"{settings.API_V1_STR}/auth/login",
            json={"email": operator_email, "password": "OperatorAnalyticsPassword1"}
        )
        assert operator_login_response.status_code == 200
        operator_token = operator_login_response.json()["access_token"]
        
        # OPERATORが再集計実行を試行（403エラー）
        response = client.post(
            f"{settings.API_V1_STR}/query-analytics/rebuild",
            headers={"Authorization": f"Bearer {operator_token}"},
            params={
                "locale": "ja",
                "period": "month",
                "top_k": 10
            }
        )
        assert response.status_code == 403
    finally:
        await cleanup_test_data(db_session, admin_email, tenant_domain)


@pytest.mark.asyncio
async def test_get_top_queries_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: トップクエリランキング取得（OPERATOR以上）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"topqueries-analytics-{unique_id}@example.com"
    password = "TopQueriesAnalyticsPassword1"
    tenant_name = f"TopQueries Analytics Tenant {unique_id}"
    tenant_domain = f"topqueries-analytics-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # トップクエリランキング取得
        response = client.get(
            f"{settings.API_V1_STR}/query-analytics/top",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "month"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_top_queries_with_custom_period(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: カスタム期間でトップクエリランキング取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"topqueries-custom-{unique_id}@example.com"
    password = "TopQueriesCustomPassword1"
    tenant_name = f"TopQueries Custom Tenant {unique_id}"
    tenant_domain = f"topqueries-custom-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # カスタム期間でトップクエリランキング取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = client.get(
            f"{settings.API_V1_STR}/query-analytics/top",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "custom",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_query_clusters_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: クラスタ一覧取得（OPERATOR以上）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"clusters-analytics-{unique_id}@example.com"
    password = "ClustersAnalyticsPassword1"
    tenant_name = f"Clusters Analytics Tenant {unique_id}"
    tenant_domain = f"clusters-analytics-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # クラスタ一覧取得
        response = client.get(
            f"{settings.API_V1_STR}/query-analytics/clusters",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "month"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_rebuild_query_analytics_invalid_period(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 無効な期間で再集計実行
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"invalid-period-{unique_id}@example.com"
    password = "InvalidPeriodPassword1"
    tenant_name = f"Invalid Period Tenant {unique_id}"
    tenant_domain = f"invalid-period-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 無効な期間で再集計実行
        response = client.post(
            f"{settings.API_V1_STR}/query-analytics/rebuild",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "invalid_period",
                "top_k": 10
            }
        )
        # バリデーションエラーになるはず
        assert response.status_code in [400, 422]
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_top_queries_custom_period_missing_dates(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: カスタム期間でstart_date/end_dateが不足
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"missing-dates-{unique_id}@example.com"
    password = "MissingDatesPassword1"
    tenant_name = f"Missing Dates Tenant {unique_id}"
    tenant_domain = f"missing-dates-tenant-{unique_id}"
    
    try:
        register_response = register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        assert register_response.status_code in [200, 201], f"登録が失敗しました: {register_response.json()}"
        # 登録後に少し待機してからログインを試みる
        import time
        time.sleep(0.1)
        _, access_token = get_authenticated_client(client, email, password)
        
        # カスタム期間でstart_date/end_dateが不足
        response = client.get(
            f"{settings.API_V1_STR}/query-analytics/top",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "locale": "ja",
                "period": "custom"
                # start_date/end_dateが不足
            }
        )
        assert response.status_code == 400
        assert "start" in response.json()["detail"].lower() or "end" in response.json()["detail"].lower()
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_top_queries_no_auth(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: 認証トークンなしでトップクエリランキング取得
    """
    response = client.get(
        f"{settings.API_V1_STR}/query-analytics/top",
        params={
            "locale": "ja",
            "period": "month"
        }
    )
    assert response.status_code in [401, 403]  # FastAPIのHTTPBearerは認証トークンがない場合403を返す可能性がある

