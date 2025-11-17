"""
クエリアナリティクス バッチ実行ジョブ

このジョブは指定されたテナント・言語・期間に対して、
会話ログから自動集計（埋め込み→クラスタ→LLMラベリング）を実行します。
APScheduler等のスケジューラから呼び出すことを想定しています。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.database import AsyncSessionLocal
from app.services.query_analytics_service import QueryAnalyticsService
from app.utils.common import DateTimeUtils

Period = Literal["today", "week", "month", "custom"]


async def resolve_period(period: Period, start: datetime | None, end: datetime | None) -> tuple[datetime, datetime]:
    """
    期間を決定するユーティリティ

    引数:
        period: today/week/month/custom
        start, end: custom時の明示指定
    戻り値:
        (start, end)
    """
    now = DateTimeUtils.now()
    if period == "today":
        s = now.replace(hour=0, minute=0, second=0, microsecond=0)
        e = now
        return s, e
    if period == "week":
        return now - timedelta(days=7), now
    if period == "month":
        return now - timedelta(days=30), now
    # custom
    if not start or not end:
        raise ValueError("custom期間ではstart/endが必要です")
    return start, end


async def run_query_aggregation_job(
    tenant_id: str,
    locale: str,
    period: Period = "month",
    start: datetime | None = None,
    end: datetime | None = None,
    top_k: int = 10,
) -> None:
    """
    バッチジョブ実行
    """
    s, e = await resolve_period(period, start, end)

    async with AsyncSessionLocal() as session:  # type: AsyncSession
        try:
            service = QueryAnalyticsService(session)
            await service.rebuild(
                tenant_id=tenant_id,
                locale=locale,
                period_start=s,
                period_end=e,
                top_k=top_k,
            )
        finally:
            await session.close()


