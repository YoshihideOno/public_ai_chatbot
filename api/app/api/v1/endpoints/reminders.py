"""
リマインダー管理エンドポイント

このファイルはリマインダー機能に関するAPIエンドポイントを定義します。
リマインダーの送信、通知管理、履歴取得機能を提供します。

主な機能:
- リマインダーの一括送信（管理者専用）
- 通知一覧の取得
- 通知の既読管理
- リマインダー履歴の取得
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.services.reminder_service import ReminderService
from app.api.v1.deps import get_current_user, require_admin_role, require_platform_admin
from app.models.user import User
from app.models.reminder import Notification
from app.core.exceptions import BusinessLogicError
from app.utils.logging import BusinessLogger, ErrorLogger, logger

router = APIRouter()


@router.post("/send-reminders")
async def send_trial_reminders(
    current_user: User = Depends(require_platform_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    お試し利用期間終了前のリマインダーを一括送信
    
    プラットフォーム管理者専用の機能です。
    
    引数:
        current_user: 認証済みユーザー（プラットフォーム管理者）
        db: データベースセッション
        
    戻り値:
        dict: 送信結果サマリ
    """
    try:
        reminder_service = ReminderService(db)
        results = await reminder_service.send_trial_reminders()
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "send_trial_reminders",
            "reminder",
            tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None
        )
        
        return {
            "message": "リマインダー送信処理が完了しました",
            "results": results
        }
        
    except Exception as e:
        ErrorLogger.error(f"リマインダー一括送信エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="リマインダー送信に失敗しました"
        )


@router.get("/notifications", response_model=List[dict])
async def get_notifications(
    is_read: Optional[bool] = Query(None, description="既読状態でフィルタ"),
    limit: int = Query(50, ge=1, le=100, description="取得件数上限"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ユーザーの通知一覧を取得
    
    引数:
        is_read: 既読状態フィルタ（オプション）
        limit: 取得件数上限
        current_user: 認証済みユーザー
        db: データベースセッション
        
    戻り値:
        List[dict]: 通知一覧
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        reminder_service = ReminderService(db)
        notifications = await reminder_service.get_tenant_notifications(
            str(current_user.tenant_id),
            str(current_user.id),
            is_read,
            limit
        )
        
        # レスポンス用の辞書に変換
        notification_list = []
        for notification in notifications:
            notification_list.append({
                "id": str(notification.id),
                "tenant_id": str(notification.tenant_id),
                "user_id": str(notification.user_id) if notification.user_id else None,
                "notification_type": notification.notification_type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "read_at": notification.read_at.isoformat() if notification.read_at else None,
                "created_at": notification.created_at.isoformat()
            })
        
        return notification_list
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"通知一覧取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="通知一覧の取得に失敗しました"
        )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    通知を既読にする
    
    引数:
        notification_id: 通知ID
        current_user: 認証済みユーザー
        db: データベースセッション
        
    戻り値:
        dict: 更新完了メッセージ
    """
    try:
        reminder_service = ReminderService(db)
        success = await reminder_service.mark_notification_as_read(
            notification_id,
            str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知が見つかりません"
            )
        
        BusinessLogger.log_user_action(
            str(current_user.id),
            "mark_notification_read",
            "notification",
            tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None
        )
        
        return {"message": "通知を既読にしました"}
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"通知既読更新エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="通知の既読更新に失敗しました"
        )


@router.get("/trial-status")
async def get_trial_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    お試し利用期間の状態を取得
    
    引数:
        current_user: 認証済みユーザー
        db: データベースセッション
        
    戻り値:
        dict: お試し利用期間の状態情報
    """
    try:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="テナントに所属していません"
            )
        
        from app.services.tenant_service import TenantService
        tenant_service = TenantService(db)
        
        trial_status = await tenant_service.check_trial_period_status(str(current_user.tenant_id))
        
        return {
            "trial_status": trial_status,
            "can_use_service": await tenant_service.can_use_service(str(current_user.tenant_id))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        ErrorLogger.error(f"お試し利用期間状態取得エラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="お試し利用期間状態の取得に失敗しました"
        )
