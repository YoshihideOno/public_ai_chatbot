from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
from app.schemas.stats import (
    UsageStats, UsageTimeSeries, TopQuery, LLMUsageStats,
    FeedbackStats, StorageStats, DashboardStats, AlertRule,
    Alert, SystemHealth, MonitoringConfig
)
from app.schemas.user import User
from app.services.stats_service import StatsService, MonitoringService
from app.api.v1.deps import (
    get_current_user, 
    require_admin_role,
    get_tenant_from_user
)
from app.models.user import UserRole
from app.core.exceptions import ResourceNotFoundError, TenantAccessDeniedError
from app.utils.logging import BusinessLogger, PerformanceLogger
from app.utils.common import DateTimeUtils

router = APIRouter()


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("day"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """利用統計取得"""
    stats_service = StatsService(db)
    
    # プラットフォーム管理者の場合、tenant_idはNoneになる
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"  # Platform admin can access all tenants
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    stats = await stats_service.get_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )
    
    # 利用統計はダッシュボード表示用の参照系GETのため、監査ログには記録しない
    return stats


@router.get("/usage/time-series", response_model=UsageTimeSeries)
async def get_usage_time_series(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("day"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """利用統計時系列データ取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    time_series = await stats_service.get_usage_time_series(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        granularity=granularity
    )
    
    # 利用統計の時系列データは参照系GETのため、監査ログには記録しない
    return time_series


@router.get("/top-queries", response_model=List[TopQuery])
async def get_top_queries(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """よくある質問TOP取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    top_queries = await stats_service.get_top_queries(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    # よくある質問TOPはダッシュボード表示用の参照系GETのため、監査ログには記録しない
    return top_queries


@router.get("/llm-usage", response_model=List[LLMUsageStats])
async def get_llm_usage_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """LLM使用量統計取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    llm_stats = await stats_service.get_llm_usage_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # LLM使用量統計は参照系GETのため、監査ログには記録しない
    return llm_stats


@router.get("/feedback", response_model=FeedbackStats)
async def get_feedback_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """評価統計取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    feedback_stats = await stats_service.get_feedback_stats(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # 評価統計は参照系GETのため、監査ログには記録しない
    return feedback_stats


@router.get("/storage", response_model=StorageStats)
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ストレージ統計取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    storage_stats = await stats_service.get_storage_stats(tenant_id)
    
    # ストレージ統計は参照系GETのため、監査ログには記録しない
    return storage_stats


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    period: str = Query("month"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ダッシュボード統計取得"""
    stats_service = StatsService(db)
    
    # プラットフォーム管理者の場合、tenant_idはNoneになる
    # その場合はデフォルトのテナントIDとして"system"を使用
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"  # Platform admin can access all tenants
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    
    dashboard_stats = await stats_service.get_dashboard_stats(
        tenant_id=tenant_id,
        period=period
    )
    
    # ダッシュボード統計は画面表示用の参照系GETのため、監査ログには記録しない
    return dashboard_stats


@router.get("/export/csv")
async def export_stats_csv(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    metric_type: str = Query("usage"),
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """統計データCSVエクスポート"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    stats_service = StatsService(db)
    
    # デフォルト期間設定
    if not end_date:
        end_date = DateTimeUtils.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # TODO: 実際のCSVエクスポート処理を実装
    csv_data = f"""期間,{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}
メトリクス,{metric_type}
テナントID,{tenant_id}
エクスポート日時,{DateTimeUtils.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "export_stats_csv",
        "stats_export",
        tenant_id=tenant_id
    )
    
    return {
        "message": "CSVエクスポートが完了しました",
        "data": csv_data,
        "filename": f"stats_{tenant_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    }


# 監視・アラート関連エンドポイント
@router.post("/alerts/rules", response_model=AlertRule)
async def create_alert_rule(
    rule_data: AlertRule,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """アラートルール作成"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    monitoring_service = MonitoringService(db)
    
    alert_rule = await monitoring_service.create_alert_rule(
        tenant_id=tenant_id,
        rule_data=rule_data
    )
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "create_alert_rule",
        "alert_rule",
        tenant_id=tenant_id
    )
    
    return alert_rule


@router.get("/alerts", response_model=List[Alert])
async def get_alerts(
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """アラート一覧取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    monitoring_service = MonitoringService(db)
    
    alerts = await monitoring_service.check_alerts(tenant_id)
    
    # アラート一覧取得は参照系GETのため、監査ログには記録しない
    return alerts


@router.get("/health", response_model=SystemHealth)
async def get_system_health(
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """システムヘルスチェック"""
    monitoring_service = MonitoringService(db)
    
    health = await monitoring_service.get_system_health()
    
    # システムヘルスチェックは参照系GETのため、監査ログには記録しない
    return health


@router.post("/metrics")
async def log_metric(
    metric_name: str,
    value: float,
    metadata: Optional[dict] = None,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """メトリクスログ記録"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    monitoring_service = MonitoringService(db)
    
    await monitoring_service.log_metric(
        tenant_id=tenant_id,
        metric_name=metric_name,
        value=value,
        metadata=metadata or {}
    )
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "log_metric",
        "metric_log",
        tenant_id=tenant_id
    )
    
    return {"message": "メトリクスが記録されました"}


@router.get("/monitoring/config", response_model=MonitoringConfig)
async def get_monitoring_config(
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """監視設定取得"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    
    # TODO: 実際の監視設定をDBから取得
    config = MonitoringConfig(
        tenant_id=tenant_id,
        enable_monitoring=True,
        alert_rules=[],
        notification_email=None,
        notification_webhook=None,
        check_interval_minutes=5
    )
    
    # 監視設定の取得は参照系GETのため、監査ログには記録しない
    return config


@router.put("/monitoring/config", response_model=MonitoringConfig)
async def update_monitoring_config(
    config_data: MonitoringConfig,
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db)
):
    """監視設定更新"""
    if current_user.role == UserRole.PLATFORM_ADMIN:
        tenant_id = "system"
    else:
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="テナントIDが設定されていません"
            )
    
    # TODO: 実際の監視設定をDBに保存
    config_data.tenant_id = tenant_id
    
    BusinessLogger.log_user_action(
        str(current_user.id),
        "update_monitoring_config",
        "monitoring_config",
        tenant_id=tenant_id
    )
    
    return config_data
