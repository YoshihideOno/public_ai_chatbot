"""
クエリアナリティクスエンドポイント

自動集計の再実行、および集計済みデータの取得APIを提供します。
RBACにより、再集計はTENANT_ADMIN以上、取得はOPERATOR以上とします。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.v1.deps import get_current_user, require_admin_role, require_operator_or_above
from app.models.user import User
from app.services.query_analytics_service import QueryAnalyticsService
from app.models.query_analytics import QueryCluster, TopQueryAggregate
from sqlalchemy import select, and_
from app.utils.common import DateTimeUtils
from app.utils.logging import BusinessLogger


router = APIRouter()


def _resolve_period(period: str, start: Optional[datetime], end: Optional[datetime]) -> tuple[datetime, datetime]:
    now = DateTimeUtils.now()
    if period == "today":
        s = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return s, now
    if period == "week":
        return now - timedelta(days=7), now
    if period == "month":
        return now - timedelta(days=30), now
    if not start or not end:
        raise HTTPException(status_code=400, detail="custom期間ではstart/endが必要です")
    return start, end


@router.post("/rebuild")
async def rebuild_query_analytics(
    locale: str = Query(..., min_length=2, max_length=10),
    period: str = Query("month", regex="^(today|week|month|custom)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    top_k: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_admin_role()),
    db: AsyncSession = Depends(get_db),
):
    """
    クエリアナリティクスの再集計を実行（TENANT_ADMIN以上）
    """
    if not current_user.tenant_id and current_user.role != "PLATFORM_ADMIN":
        raise HTTPException(status_code=400, detail="テナントIDが必要です")

    tenant_id = "system" if current_user.role == "PLATFORM_ADMIN" else str(current_user.tenant_id)
    s, e = _resolve_period(period, start_date, end_date)

    service = QueryAnalyticsService(db)
    await service.rebuild(tenant_id=tenant_id, locale=locale, period_start=s, period_end=e, top_k=top_k)

    BusinessLogger.log_user_action(str(current_user.id), "rebuild_query_analytics", "query_analytics", tenant_id=tenant_id)
    return {"message": "再集計を実行しました"}


@router.get("/top", response_model=List[Dict[str, Any]])
async def get_top_queries(
    locale: str = Query(..., min_length=2, max_length=10),
    period: str = Query("month", regex="^(today|week|month|custom)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_operator_or_above()),
    db: AsyncSession = Depends(get_db),
):
    """
    集計済みのトップクエリランキングを取得（OPERATOR以上）
    """
    tenant_id = "system" if current_user.role == "PLATFORM_ADMIN" else str(current_user.tenant_id)
    s, e = _resolve_period(period, start_date, end_date)

    result = await db.execute(
        select(TopQueryAggregate)
        .where(
            and_(
                TopQueryAggregate.tenant_id == tenant_id,
                TopQueryAggregate.locale == locale,
                TopQueryAggregate.period_start == s,
                TopQueryAggregate.period_end == e,
            )
        )
        .order_by(TopQueryAggregate.rank.asc())
    )
    rows = result.scalars().all()
    return [
        {
            "rank": r.rank,
            "query": r.query,
            "count": r.count,
            "like_rate": float(r.like_rate),
            "avg_response_time_ms": float(r.avg_response_time_ms),
            "cluster_id": r.cluster_id,
        }
        for r in rows
    ]


@router.get("/clusters", response_model=List[Dict[str, Any]])
async def get_query_clusters(
    locale: str = Query(..., min_length=2, max_length=10),
    period: str = Query("month", regex="^(today|week|month|custom)$"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(require_operator_or_above()),
    db: AsyncSession = Depends(get_db),
):
    """
    集計済みのクラスタ一覧を取得（OPERATOR以上）
    """
    tenant_id = "system" if current_user.role == "PLATFORM_ADMIN" else str(current_user.tenant_id)
    s, e = _resolve_period(period, start_date, end_date)

    result = await db.execute(
        select(QueryCluster)
        .where(
            and_(
                QueryCluster.tenant_id == tenant_id,
                QueryCluster.locale == locale,
                QueryCluster.period_start == s,
                QueryCluster.period_end == e,
            )
        )
        .order_by(QueryCluster.cluster_id.asc())
    )
    rows = result.scalars().all()
    return [
        {
            "cluster_id": r.cluster_id,
            "label": r.label,
            "confidence": float(r.confidence),
            "sample_queries": r.sample_queries,
        }
        for r in rows
    ]


