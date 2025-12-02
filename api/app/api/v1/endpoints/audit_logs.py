"""
監査ログエンドポイント

このファイルはダッシュボード用の最近の活動（監査ログ）取得APIを提供する。
認証済みユーザーのみアクセス可能で、テナント分離（RLS相当）を適用する。
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from typing import Optional, List

from app.core.database import get_db
from app.schemas.user import User
from app.api.v1.deps import get_current_user
from app.models.user import UserRole
from app.utils.logging import BusinessLogger
from app.services.audit_log_service import AuditLogService

from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/recent")
async def get_recent_audit_logs(
    limit: int = Query(10, ge=1, le=50),
    skip_audit: bool = Query(False, description="監査ログ記録をスキップするかどうか（自動ポーリング時はtrue）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """最近の監査ログを取得
    
    - 認証必須
    - テナント分離: PLATFORM_ADMIN は全件、それ以外は自テナントのみ
    - limit: 1〜50
    - skip_audit: 監査ログ記録をスキップするかどうか（デフォルト: false）
      - true: 自動ポーリング時など、監査ログ記録をスキップ
      - false: 初回取得時など、監査ログ記録を実行
    
    メモ:
        ダッシュボードの自動更新による監査ログ肥大化を防ぐため、
        「初回取得（skip_audit=false）のみ」自分自身の取得イベントをaudit_logsに記録する。
    """

    stmt = select(
        AuditLog.id,
        AuditLog.user_id,
        AuditLog.tenant_id,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.ip_address,
        AuditLog.user_agent,
        AuditLog.details,
        AuditLog.created_at
    )

    if current_user.role != UserRole.PLATFORM_ADMIN:
        if not current_user.tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="テナントIDが設定されていません")
        stmt = stmt.where(AuditLog.tenant_id == current_user.tenant_id)

    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit)

    result = await db.execute(stmt)
    rows = result.all()

    # 監査: 取得イベントを記録（skip_auditがFalseの場合のみ）
    if not skip_audit:
        # テスト環境でも動作するように、直接AuditLogServiceを使用
        if current_user.tenant_id:
            try:
                audit_service = AuditLogService(db)
                await audit_service.create_audit_log(
                    tenant_id=str(current_user.tenant_id),
                    action="get_recent_audit_logs",
                    resource_type="audit_logs",
                    user_id=str(current_user.id)
                )
            except Exception as e:
                # 監査ログ記録の失敗はメイン処理に影響させない
                # エラーはログに記録（BusinessLoggerは使用しない）
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    f"監査ログの記録に失敗: action=get_recent_audit_logs, "
                    f"tenant_id={current_user.tenant_id}, error={str(e)}",
                    exc_info=True
                )

    # JSON化
    activities = []
    for r in rows:
        activities.append({
            "id": str(r.id),
            "user_id": str(r.user_id) if r.user_id else None,
            "tenant_id": str(r.tenant_id) if r.tenant_id else None,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": str(r.resource_id) if r.resource_id else None,
            "ip_address": str(r.ip_address) if r.ip_address else None,
            "user_agent": r.user_agent,
            "details": r.details if r.details else {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"activities": activities}


