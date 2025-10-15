from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from app.models.conversation import Conversation
from app.models.usage_log import UsageLog
from app.models.file import File
from app.models.user import User
from app.schemas.stats import (
    UsageStats, UsageTimeSeries, TopQuery, LLMUsageStats,
    LLMUsageTimeSeries, FeedbackStats, FeedbackAnalysis,
    StorageStats, DashboardStats, AlertRule, Alert,
    MonitoringConfig, HealthCheck, SystemHealth
)
from app.utils.logging import BusinessLogger, PerformanceLogger, MonitoringUtils
from app.utils.common import DateTimeUtils


class StatsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_usage_stats(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        granularity: str = "day"
    ) -> UsageStats:
        """利用統計取得"""
        try:
            # 総質問数
            total_queries_result = await self.db.execute(
                select(func.count(Conversation.id))
                .where(
                    and_(
                        Conversation.tenant_id == tenant_id,
                        Conversation.created_at >= start_date,
                        Conversation.created_at <= end_date
                    )
                )
            )
            total_queries = total_queries_result.scalar() or 0
            
            # ユニークユーザー数（セッションIDベース）
            unique_users_result = await self.db.execute(
                select(func.count(func.distinct(Conversation.session_id)))
                .where(
                    and_(
                        Conversation.tenant_id == tenant_id,
                        Conversation.created_at >= start_date,
                        Conversation.created_at <= end_date
                    )
                )
            )
            unique_users = unique_users_result.scalar() or 0
            
            # 平均応答時間（仮の値）
            avg_response_time_ms = 3200.0  # TODO: 実際の計算
            
            # 評価率（仮の値）
            feedback_rate = 0.72  # TODO: 実際の計算
            like_rate = 0.65  # TODO: 実際の計算
            
            return UsageStats(
                tenant_id=tenant_id,
                metric_type="queries",
                granularity=granularity,
                start_date=start_date,
                end_date=end_date,
                total_queries=total_queries,
                unique_users=unique_users,
                avg_response_time_ms=avg_response_time_ms,
                feedback_rate=feedback_rate,
                like_rate=like_rate
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_usage_stats",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_usage_time_series(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        granularity: str = "day"
    ) -> UsageTimeSeries:
        """利用統計時系列データ取得"""
        try:
            # TODO: 実際の時系列データを取得
            # 現在は仮のデータを返す
            
            time_series_data = []
            current_date = start_date
            
            while current_date <= end_date:
                # 仮のデータ生成
                queries_count = await self._get_queries_count_for_date(
                    tenant_id, current_date
                )
                
                time_series_data.append({
                    "timestamp": current_date,
                    "value": float(queries_count),
                    "metadata": {}
                })
                
                # 次の期間に移動
                if granularity == "hour":
                    current_date += timedelta(hours=1)
                elif granularity == "day":
                    current_date += timedelta(days=1)
                elif granularity == "week":
                    current_date += timedelta(weeks=1)
                elif granularity == "month":
                    current_date += timedelta(days=30)
            
            return UsageTimeSeries(
                queries=time_series_data,
                users=[],  # TODO: 実装
                response_time=[],  # TODO: 実装
                feedback_rate=[]  # TODO: 実装
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_usage_time_series",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_top_queries(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 10
    ) -> List[TopQuery]:
        """よくある質問TOP取得"""
        try:
            # TODO: 実際の集計処理を実装
            # 現在は仮のデータを返す
            
            top_queries = [
                TopQuery(
                    query="返品方法を教えてください",
                    count=89,
                    like_rate=0.85,
                    avg_response_time_ms=2800.0
                ),
                TopQuery(
                    query="配送期間はどのくらいですか",
                    count=67,
                    like_rate=0.78,
                    avg_response_time_ms=3200.0
                ),
                TopQuery(
                    query="支払い方法を変更できますか",
                    count=54,
                    like_rate=0.72,
                    avg_response_time_ms=2900.0
                ),
                TopQuery(
                    query="注文をキャンセルしたいです",
                    count=42,
                    like_rate=0.68,
                    avg_response_time_ms=3500.0
                ),
                TopQuery(
                    query="問い合わせ先を教えてください",
                    count=38,
                    like_rate=0.91,
                    avg_response_time_ms=2100.0
                )
            ]
            
            return top_queries[:limit]
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_top_queries",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_llm_usage_stats(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[LLMUsageStats]:
        """LLM使用量統計取得"""
        try:
            # TODO: 実際のLLM使用量データを取得
            # 現在は仮のデータを返す
            
            llm_stats = [
                LLMUsageStats(
                    tenant_id=tenant_id,
                    model="gpt-4",
                    total_tokens_in=125000,
                    total_tokens_out=85000,
                    total_cost=125.50,
                    request_count=450,
                    avg_tokens_per_request=467.0
                ),
                LLMUsageStats(
                    tenant_id=tenant_id,
                    model="gpt-3.5-turbo",
                    total_tokens_in=89000,
                    total_tokens_out=56000,
                    total_cost=45.20,
                    request_count=320,
                    avg_tokens_per_request=453.0
                )
            ]
            
            return llm_stats
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_llm_usage_stats",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_feedback_stats(
        self, 
        tenant_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> FeedbackStats:
        """評価統計取得"""
        try:
            # TODO: 実際の評価データを取得
            # 現在は仮のデータを返す
            
            return FeedbackStats(
                tenant_id=tenant_id,
                total_feedback=1250,
                positive_feedback=900,
                negative_feedback=100,
                no_feedback=250,
                positive_rate=0.72
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_feedback_stats",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_storage_stats(self, tenant_id: str) -> StorageStats:
        """ストレージ統計取得"""
        try:
            # 総ファイル数
            total_files_result = await self.db.execute(
                select(func.count(File.id))
                .where(
                    and_(
                        File.tenant_id == tenant_id,
                        File.deleted_at.is_(None)
                    )
                )
            )
            total_files = total_files_result.scalar() or 0
            
            # 総サイズ
            total_size_result = await self.db.execute(
                select(func.sum(File.size_bytes))
                .where(
                    and_(
                        File.tenant_id == tenant_id,
                        File.deleted_at.is_(None)
                    )
                )
            )
            total_size_bytes = total_size_result.scalar() or 0
            
            # 総チャンク数
            total_chunks_result = await self.db.execute(
                select(func.count())
                .select_from(File)
                .join(File.chunks)
                .where(
                    and_(
                        File.tenant_id == tenant_id,
                        File.deleted_at.is_(None)
                    )
                )
            )
            total_chunks = total_chunks_result.scalar() or 0
            
            # ストレージ制限（仮の値）
            storage_limit_mb = 100
            
            return StorageStats(
                tenant_id=tenant_id,
                total_files=total_files,
                total_size_mb=total_size_bytes / (1024 * 1024),
                total_chunks=total_chunks,
                storage_limit_mb=storage_limit_mb,
                usage_percentage=(total_size_bytes / (1024 * 1024)) / storage_limit_mb * 100
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_storage_stats",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_dashboard_stats(
        self, 
        tenant_id: str, 
        period: str = "month"
    ) -> DashboardStats:
        """ダッシュボード統計取得"""
        try:
            # 期間設定
            end_date = datetime.utcnow()
            if period == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=30)
            
            # 各統計を取得
            usage_stats = await self.get_usage_stats(
                tenant_id, start_date, end_date
            )
            
            llm_usage = await self.get_llm_usage_stats(
                tenant_id, start_date, end_date
            )
            
            storage_stats = await self.get_storage_stats(tenant_id)
            
            top_queries = await self.get_top_queries(
                tenant_id, start_date, end_date, limit=5
            )
            
            # 最近の活動（仮のデータ）
            recent_activity = [
                {
                    "type": "conversation",
                    "description": "新しい質問が投稿されました",
                    "timestamp": datetime.utcnow() - timedelta(minutes=5),
                    "details": {"query": "返品方法について"}
                },
                {
                    "type": "file_upload",
                    "description": "ファイルがアップロードされました",
                    "timestamp": datetime.utcnow() - timedelta(hours=1),
                    "details": {"filename": "FAQ.pdf"}
                }
            ]
            
            return DashboardStats(
                tenant_id=tenant_id,
                period=period,
                usage_stats=usage_stats,
                llm_usage=llm_usage,
                storage_stats=storage_stats,
                top_queries=top_queries,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_dashboard_stats",
                0,
                tenant_id=tenant_id
            )
            raise

    async def _get_queries_count_for_date(
        self, 
        tenant_id: str, 
        target_date: datetime
    ) -> int:
        """指定日の質問数を取得"""
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        result = await self.db.execute(
            select(func.count(Conversation.id))
            .where(
                and_(
                    Conversation.tenant_id == tenant_id,
                    Conversation.created_at >= start_of_day,
                    Conversation.created_at < end_of_day
                )
            )
        )
        
        return result.scalar() or 0


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_alert_rule(
        self, 
        tenant_id: str, 
        rule_data: AlertRule
    ) -> AlertRule:
        """アラートルール作成"""
        try:
            # TODO: アラートルールをDBに保存
            rule_data.tenant_id = tenant_id
            
            BusinessLogger.log_tenant_action(
                tenant_id,
                "create_alert_rule",
                {"rule_name": rule_data.name}
            )
            
            return rule_data
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "create_alert_rule",
                0,
                tenant_id=tenant_id
            )
            raise

    async def check_alerts(self, tenant_id: str) -> List[Alert]:
        """アラートチェック"""
        try:
            # TODO: 実際のアラートチェック処理
            alerts = []
            
            # ストレージ使用量チェック
            storage_stats = await StatsService(self.db).get_storage_stats(tenant_id)
            if storage_stats.usage_percentage > 80:
                alerts.append(Alert(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    rule_id="storage_usage",
                    metric_type="storage",
                    current_value=storage_stats.usage_percentage,
                    threshold=80.0,
                    message=f"ストレージ使用量が{storage_stats.usage_percentage:.1f}%に達しました",
                    severity="medium",
                    triggered_at=datetime.utcnow(),
                    is_resolved=False
                ))
            
            return alerts
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "check_alerts",
                0,
                tenant_id=tenant_id
            )
            raise

    async def get_system_health(self) -> SystemHealth:
        """システムヘルスチェック"""
        try:
            services = []
            
            # データベースヘルスチェック
            db_start = datetime.utcnow()
            await self.db.execute(select(1))
            db_duration = (datetime.utcnow() - db_start).total_seconds() * 1000
            
            services.append(HealthCheck(
                service="database",
                status="healthy" if db_duration < 100 else "degraded",
                response_time_ms=db_duration,
                last_check=datetime.utcnow(),
                details={"connection": "active"}
            ))
            
            # TODO: 他のサービスのヘルスチェック
            
            overall_status = "healthy"
            if any(s.status == "unhealthy" for s in services):
                overall_status = "unhealthy"
            elif any(s.status == "degraded" for s in services):
                overall_status = "degraded"
            
            return SystemHealth(
                overall_status=overall_status,
                services=services,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "get_system_health",
                0
            )
            raise

    async def log_metric(
        self, 
        tenant_id: str, 
        metric_name: str, 
        value: float, 
        metadata: Dict[str, Any] = None
    ):
        """メトリクスログ記録"""
        try:
            # TODO: メトリクスを時系列DBに保存
            MonitoringUtils.log_resource_usage(
                metric_name,
                value,
                100.0,  # 仮の制限値
                tenant_id=tenant_id
            )
            
        except Exception as e:
            PerformanceLogger.log_api_performance(
                "log_metric",
                0,
                tenant_id=tenant_id
            )
            raise
