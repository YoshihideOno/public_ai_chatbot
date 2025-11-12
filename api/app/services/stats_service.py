from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
from app.models.conversation import Conversation
from app.models.usage_log import UsageLog
from app.models.file import File, FileStatus
from app.models.user import User
from app.models.query_analytics import TopQueryAggregate
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
            # プラットフォーム管理者の場合（tenant_id="system"）、全テナントの統計を取得
            if tenant_id == "system":
                # 総質問数（全テナント）
                total_queries_result = await self.db.execute(
                    select(func.count(Conversation.id))
                    .where(
                        and_(
                            Conversation.created_at >= start_date,
                            Conversation.created_at <= end_date
                        )
                    )
                )
            else:
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
            if tenant_id == "system":
                unique_users_result = await self.db.execute(
                    select(func.count(func.distinct(Conversation.session_id)))
                    .where(
                        and_(
                            Conversation.created_at >= start_date,
                            Conversation.created_at <= end_date
                        )
                    )
                )
            else:
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
                tenant_id=tenant_id if tenant_id != "system" else "all",
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
            from app.utils.logging import logger
            logger.error(f"利用統計取得エラー: {str(e)}")
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
            # まずは事前集計テーブルから取得（存在すれば利用）
            # localeは現状未保持のため、テナント単位で期間一致の集計を参照
            aggregates_result = await self.db.execute(
                select(TopQueryAggregate)
                .where(
                    and_(
                        TopQueryAggregate.tenant_id == tenant_id,
                        TopQueryAggregate.period_start == start_date,
                        TopQueryAggregate.period_end == end_date,
                    )
                )
                .order_by(TopQueryAggregate.rank.asc())
            )
            aggregates = aggregates_result.scalars().all()
            if aggregates:
                return [
                    TopQuery(
                        query=a.query,
                        count=a.count or 0,
                        like_rate=float(a.like_rate or 0.0),
                        avg_response_time_ms=float(a.avg_response_time_ms or 0.0),
                    )
                    for a in aggregates[:limit]
                ]

            # フォールバック: Conversationから簡易集計
            fallback = await self.db.execute(
                select(
                    Conversation.user_input.label("query"),
                    func.count(Conversation.id).label("count"),
                    func.avg(Conversation.latency_ms).label("avg_response_time_ms"),
                    func.avg(
                        case(
                            (Conversation.feedback.in_(["positive", "like", "LIKE", "POSITIVE"]), 1),
                            else_=0,
                        )
                    ).label("like_rate"),
                )
                .where(
                    and_(
                        Conversation.tenant_id == tenant_id,
                        Conversation.created_at >= start_date,
                        Conversation.created_at <= end_date,
                    )
                )
                .group_by(Conversation.user_input)
                .order_by(desc("count"))
            )
            rows = fallback.fetchall()
            return [
                TopQuery(
                    query=(row.query or "").strip()[:500],
                    count=int(row.count or 0),
                    like_rate=float(row.like_rate or 0.0),
                    avg_response_time_ms=float(row.avg_response_time_ms or 0.0),
                )
                for row in rows[:limit]
            ]
            
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
            # プラットフォーム管理者の場合（tenant_id="system"）、全テナントの統計を取得
            if tenant_id == "system":
                # 総ファイル数（全テナント）
                total_files_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(File.deleted_at.is_(None))
                )
                total_files = total_files_result.scalar() or 0
                
                # 総サイズ（全テナント）
                total_size_result = await self.db.execute(
                    select(func.sum(File.size_bytes))
                    .where(File.deleted_at.is_(None))
                )
                total_size_bytes = total_size_result.scalar() or 0
                
                # 総チャンク数（全テナント）
                total_chunks_result = await self.db.execute(
                    select(func.count())
                    .select_from(File)
                    .join(File.chunks)
                    .where(File.deleted_at.is_(None))
                )
                total_chunks = total_chunks_result.scalar() or 0

                # ステータス別件数（全テナント）
                indexed_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.deleted_at.is_(None),
                            File.status == FileStatus.INDEXED
                        )
                    )
                )
                indexed_files = indexed_count_result.scalar() or 0

                processing_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.deleted_at.is_(None),
                            File.status == FileStatus.PROCESSING
                        )
                    )
                )
                processing_files = processing_count_result.scalar() or 0

                failed_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.deleted_at.is_(None),
                            File.status == FileStatus.FAILED
                        )
                    )
                )
                failed_files = failed_count_result.scalar() or 0
            else:
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

                # ステータス別件数（テナント別）
                indexed_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.tenant_id == tenant_id,
                            File.deleted_at.is_(None),
                            File.status == FileStatus.INDEXED
                        )
                    )
                )
                indexed_files = indexed_count_result.scalar() or 0

                processing_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.tenant_id == tenant_id,
                            File.deleted_at.is_(None),
                            File.status == FileStatus.PROCESSING
                        )
                    )
                )
                processing_files = processing_count_result.scalar() or 0

                failed_count_result = await self.db.execute(
                    select(func.count(File.id))
                    .where(
                        and_(
                            File.tenant_id == tenant_id,
                            File.deleted_at.is_(None),
                            File.status == FileStatus.FAILED
                        )
                    )
                )
                failed_files = failed_count_result.scalar() or 0
            
            # ストレージ制限（仮の値）
            storage_limit_mb = 100
            
            return StorageStats(
                tenant_id=tenant_id if tenant_id != "system" else "all",
                total_files=total_files,
                total_size_mb=total_size_bytes / (1024 * 1024) if total_size_bytes else 0.0,
                total_chunks=total_chunks,
                storage_limit_mb=storage_limit_mb,
                usage_percentage=(total_size_bytes / (1024 * 1024)) / storage_limit_mb * 100 if total_size_bytes and storage_limit_mb > 0 else 0.0,
                indexed_files=indexed_files if 'indexed_files' in locals() else 0,
                processing_files=processing_files if 'processing_files' in locals() else 0,
                failed_files=failed_files if 'failed_files' in locals() else 0
            )
            
        except Exception as e:
            from app.utils.logging import logger
            logger.error(f"ストレージ統計取得エラー: {str(e)}")
            raise

    async def get_dashboard_stats(
        self, 
        tenant_id: str, 
        period: str = "month"
    ) -> DashboardStats:
        """ダッシュボード統計取得"""
        try:
            # 期間設定
            end_date = DateTimeUtils.now()
            if period == "today":
                start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "week":
                start_date = end_date - timedelta(days=7)
            elif period == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=30)
            
            # デフォルト値（失敗時のフォールバック）
            usage_stats_default = UsageStats(
                tenant_id=tenant_id if tenant_id != "system" else "all",
                metric_type="queries",
                granularity="day",
                start_date=start_date,
                end_date=end_date,
                total_queries=0,
                unique_users=0,
                avg_response_time_ms=0.0,
                feedback_rate=0.0,
                like_rate=0.0,
            )
            storage_stats_default = StorageStats(
                tenant_id=tenant_id if tenant_id != "system" else "all",
                total_files=0,
                total_size_mb=0.0,
                total_chunks=0,
                storage_limit_mb=100,
                usage_percentage=0.0,
            )
            llm_usage: List[LLMUsageStats] = []
            top_queries: List[TopQuery] = []

            # 各統計を取得（個別に例外処理して継続）
            try:
                usage_stats = await self.get_usage_stats(
                    tenant_id, start_date, end_date
                )
            except Exception as e:  # noqa: BLE001
                from app.utils.logging import logger
                logger.error(f"ダッシュボード: usage_stats 取得エラー: {str(e)}")
                usage_stats = usage_stats_default

            try:
                llm_usage = await self.get_llm_usage_stats(
                    tenant_id, start_date, end_date
                )
            except Exception as e:  # noqa: BLE001
                from app.utils.logging import logger
                logger.error(f"ダッシュボード: llm_usage 取得エラー: {str(e)}")
                llm_usage = []

            try:
                storage_stats = await self.get_storage_stats(tenant_id)
            except Exception as e:  # noqa: BLE001
                from app.utils.logging import logger
                logger.error(f"ダッシュボード: storage_stats 取得エラー: {str(e)}")
                storage_stats = storage_stats_default

            try:
                top_queries = await self.get_top_queries(
                    tenant_id, start_date, end_date, limit=5
                )
            except Exception as e:  # noqa: BLE001
                from app.utils.logging import logger
                logger.error(f"ダッシュボード: top_queries 取得エラー: {str(e)}")
                top_queries = []
            
            # 最近の活動（仮のデータ）
            recent_activity = [
                {
                    "type": "conversation",
                    "description": "新しい質問が投稿されました",
                    "timestamp": DateTimeUtils.now() - timedelta(minutes=5),
                    "details": {"query": "返品方法について"}
                },
                {
                    "type": "file_upload",
                    "description": "ファイルがアップロードされました",
                    "timestamp": DateTimeUtils.now() - timedelta(hours=1),
                    "details": {"filename": "FAQ.pdf"}
                }
            ]
            
            return DashboardStats(
                tenant_id=tenant_id if tenant_id != "system" else "all",
                period=period,
                usage_stats=usage_stats,
                llm_usage=llm_usage,
                storage_stats=storage_stats,
                top_queries=top_queries,
                recent_activity=recent_activity
            )
            
        except Exception as e:
            # エラーログを出力（PerformanceLoggerは使用しない）
            from app.utils.logging import logger
            logger.error(f"ダッシュボード統計取得エラー: {str(e)}")
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
                    triggered_at=DateTimeUtils.now(),
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
            db_start = DateTimeUtils.now()
            await self.db.execute(select(1))
            db_duration = (DateTimeUtils.now() - db_start).total_seconds() * 1000
            
            services.append(HealthCheck(
                service="database",
                status="healthy" if db_duration < 100 else "degraded",
                response_time_ms=db_duration,
                last_check=DateTimeUtils.now(),
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
                timestamp=DateTimeUtils.now()
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
