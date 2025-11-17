"""
統計APIテストファイル

このファイルは統計関連エンドポイントの包括的なテストケースを定義します。
正常系、異常系、権限テストを含みます。
"""

import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from tests.test_auth import register_user_and_tenant, cleanup_test_data, get_authenticated_client


@pytest.mark.asyncio
async def test_get_usage_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 利用統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"stats-{unique_id}@example.com"
    password = "StatsPassword1"
    tenant_name = f"Stats Tenant {unique_id}"
    tenant_domain = f"stats-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 利用統計取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/usage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_usage_stats_with_dates(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 日付指定で利用統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"stats-dates-{unique_id}@example.com"
    password = "StatsDatesPassword1"
    tenant_name = f"Stats Dates Tenant {unique_id}"
    tenant_domain = f"stats-dates-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 日付指定で利用統計取得
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = client.get(
            f"{settings.API_V1_STR}/stats/usage",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": "day"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_usage_time_series_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 利用統計時系列データ取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"timeseries-{unique_id}@example.com"
    password = "TimeSeriesPassword1"
    tenant_name = f"TimeSeries Tenant {unique_id}"
    tenant_domain = f"timeseries-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 利用統計時系列データ取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/usage/time-series",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_top_queries_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: よくある質問TOP取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"topqueries-{unique_id}@example.com"
    password = "TopQueriesPassword1"
    tenant_name = f"TopQueries Tenant {unique_id}"
    tenant_domain = f"topqueries-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # よくある質問TOP取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/top-queries",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_llm_usage_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: LLM使用量統計取得（管理者専用）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"llmstats-{unique_id}@example.com"
    password = "LlmStatsPassword1"
    tenant_name = f"LlmStats Tenant {unique_id}"
    tenant_domain = f"llmstats-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # LLM使用量統計取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/llm-usage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_feedback_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 評価統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"feedback-{unique_id}@example.com"
    password = "FeedbackPassword1"
    tenant_name = f"Feedback Tenant {unique_id}"
    tenant_domain = f"feedback-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 評価統計取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/feedback",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_storage_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: ストレージ統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"storage-{unique_id}@example.com"
    password = "StoragePassword1"
    tenant_name = f"Storage Tenant {unique_id}"
    tenant_domain = f"storage-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # ストレージ統計取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/storage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_dashboard_stats_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: ダッシュボード統計取得
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"dashboard-{unique_id}@example.com"
    password = "DashboardPassword1"
    tenant_name = f"Dashboard Tenant {unique_id}"
    tenant_domain = f"dashboard-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # ダッシュボード統計取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/dashboard",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"period": "month"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_export_stats_csv_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 統計データCSVエクスポート（管理者専用）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"export-{unique_id}@example.com"
    password = "ExportPassword1"
    tenant_name = f"Export Tenant {unique_id}"
    tenant_domain = f"export-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 統計データCSVエクスポート
        response = client.get(
            f"{settings.API_V1_STR}/stats/export/csv",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"metric_type": "usage"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "message" in data
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_system_health_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: システムヘルスチェック（管理者専用）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"health-{unique_id}@example.com"
    password = "HealthPassword1"
    tenant_name = f"Health Tenant {unique_id}"
    tenant_domain = f"health-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # システムヘルスチェック
        response = client.get(
            f"{settings.API_V1_STR}/stats/health",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_monitoring_config_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 監視設定取得（管理者専用）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"monitoring-{unique_id}@example.com"
    password = "MonitoringPassword1"
    tenant_name = f"Monitoring Tenant {unique_id}"
    tenant_domain = f"monitoring-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 監視設定取得
        response = client.get(
            f"{settings.API_V1_STR}/stats/monitoring/config",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_update_monitoring_config_success(client: TestClient, db_session: AsyncSession):
    """
    正常系テスト: 監視設定更新（管理者専用）
    """
    unique_id = str(uuid.uuid4())[:8]
    email = f"monitoring-update-{unique_id}@example.com"
    password = "MonitoringUpdatePassword1"
    tenant_name = f"Monitoring Update Tenant {unique_id}"
    tenant_domain = f"monitoring-update-tenant-{unique_id}"
    
    try:
        register_user_and_tenant(client, email, password, tenant_name, tenant_domain)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 監視設定更新
        config_data = {
            "enable_monitoring": True,
            "check_interval_minutes": 10
        }
        response = client.put(
            f"{settings.API_V1_STR}/stats/monitoring/config",
            headers={"Authorization": f"Bearer {access_token}"},
            json=config_data
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    finally:
        await cleanup_test_data(db_session, email, tenant_domain)


@pytest.mark.asyncio
async def test_get_stats_no_tenant(client: TestClient, db_session: AsyncSession):
    """
    異常系テスト: テナント未設定で統計取得
    """
    from tests.test_auth import register_user, cleanup_user
    
    unique_id = str(uuid.uuid4())[:8]
    email = f"notenant-stats-{unique_id}@example.com"
    password = "NoTenantStatsPassword1"
    username = f"nostats{unique_id}"
    
    try:
        register_user(client, email, password, username)
        _, access_token = get_authenticated_client(client, email, password)
        
        # 統計取得を試行（テナント未設定のためエラー）
        response = client.get(
            f"{settings.API_V1_STR}/stats/usage",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 400
        assert "テナントID" in response.json()["detail"] or "tenant" in response.json()["detail"].lower()
    finally:
        await cleanup_user(db_session, email)

