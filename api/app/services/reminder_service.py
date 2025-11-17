"""
リマインダー管理サービス

このファイルはリマインダー機能に関するビジネスロジックを実装します。
お試し利用期間終了前のリマインダー送信、通知管理などの機能を提供します。

主な機能:
- リマインダーの送信処理
- メール・ダッシュボード通知の管理
- リマインダー送信履歴の管理
- バッチ処理用のリマインダー検索
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.models.reminder import ReminderLog, Notification
from app.models.tenant import Tenant
from app.models.user import User
from app.services.tenant_service import TenantService
from app.services.email_service import EmailService
from app.core.constants import ReminderSettings, SystemMessages
from app.core.exceptions import BusinessLogicError
from app.utils.common import DateTimeUtils
from app.utils.logging import BusinessLogger, ErrorLogger, logger


class ReminderService:
    """
    リマインダー管理サービス
    
    リマインダーに関する全てのビジネスロジックを担当します。
    メール送信、通知作成、履歴管理などを統合的に管理します。
    
    属性:
        db: データベースセッション（AsyncSession）
    """
    
    def __init__(self, db: AsyncSession):
        """
        初期化
        
        引数:
            db: データベースセッション
        """
        self.db = db
        self.tenant_service = TenantService(db)
        self.email_service = EmailService()
    
    async def send_trial_reminders(self) -> Dict[str, Any]:
        """
        お試し利用期間終了前のリマインダーを一括送信
        
        戻り値:
            Dict[str, Any]: 送信結果サマリ
        """
        try:
            # リマインダー対象のテナントを取得
            reminder_targets = await self._get_reminder_targets()
            
            results = {
                "total_tenants": len(reminder_targets),
                "email_sent": 0,
                "notifications_created": 0,
                "errors": []
            }
            
            for tenant_info in reminder_targets:
                try:
                    # メールリマインダー送信
                    email_sent = await self._send_email_reminder(tenant_info)
                    if email_sent:
                        results["email_sent"] += 1
                    
                    # ダッシュボード通知作成
                    notification_created = await self._create_dashboard_notification(tenant_info)
                    if notification_created:
                        results["notifications_created"] += 1
                        
                except Exception as e:
                    error_msg = f"テナント {tenant_info['tenant_id']} のリマインダー送信エラー: {str(e)}"
                    results["errors"].append(error_msg)
                    logger.error(error_msg)
            
            logger.info(f"リマインダー一括送信完了: {results}")
            return results
            
        except Exception as e:
            logger.error(f"リマインダー一括送信エラー: {str(e)}")
            raise
    
    async def _get_reminder_targets(self) -> List[Dict[str, Any]]:
        """
        リマインダー対象のテナント一覧を取得
        
        戻り値:
            List[Dict[str, Any]]: リマインダー対象テナント情報
        """
        try:
            # ナレッジ登録済みのテナントを取得
            query = select(Tenant).where(
                and_(
                    Tenant.knowledge_registered_at.isnot(None),
                    Tenant.status == "ACTIVE"
                )
            ).options(selectinload(Tenant.users))
            
            result = await self.db.execute(query)
            tenants = result.scalars().all()
            
            reminder_targets = []
            reminder_days = ReminderSettings.get_reminder_days()
            
            for tenant in tenants:
                # お試し利用期間の状態をチェック
                trial_status = await self.tenant_service.check_trial_period_status(str(tenant.id))
                
                if not trial_status["is_trial_active"]:
                    continue
                
                days_remaining = trial_status["days_remaining"]
                
                # リマインダー対象日数に該当するかチェック
                for reminder_day in reminder_days:
                    if days_remaining == reminder_day:
                        # 既にリマインダーを送信済みかチェック
                        already_sent = await self._check_reminder_sent(
                            str(tenant.id), 
                            reminder_day
                        )
                        
                        if not already_sent:
                            # テナント管理者を取得
                            admin_user = next(
                                (user for user in tenant.users if user.role.value == "TENANT_ADMIN"), 
                                None
                            )
                            
                            if admin_user:
                                reminder_targets.append({
                                    "tenant_id": str(tenant.id),
                                    "tenant_name": tenant.name,
                                    "admin_email": admin_user.email,
                                    "admin_username": admin_user.username,
                                    "days_remaining": days_remaining,
                                    "trial_end_date": trial_status["trial_end_date"]
                                })
            
            return reminder_targets
            
        except Exception as e:
            logger.error(f"リマインダー対象取得エラー: {str(e)}")
            raise
    
    async def _check_reminder_sent(self, tenant_id: str, days_before_expiry: int) -> bool:
        """
        指定日数のリマインダーが既に送信済みかチェック
        
        引数:
            tenant_id: テナントID
            days_before_expiry: 終了何日前のリマインダーか
        戻り値:
            bool: 送信済みの場合True
        """
        try:
            query = select(ReminderLog).where(
                and_(
                    ReminderLog.tenant_id == tenant_id,
                    ReminderLog.days_before_expiry == str(days_before_expiry),
                    ReminderLog.is_sent == True
                )
            )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"リマインダー送信済みチェックエラー: {str(e)}")
            return False
    
    async def _send_email_reminder(self, tenant_info: Dict[str, Any]) -> bool:
        """
        メールリマインダーを送信
        
        引数:
            tenant_info: テナント情報
        戻り値:
            bool: 送信成功時True
        """
        try:
            # リマインダーメッセージを生成
            message = SystemMessages.TRIAL_REMINDER_MESSAGE.format(
                remaining_days=tenant_info["days_remaining"]
            )
            
            # メール送信
            email_sent = await self.email_service.send_trial_reminder_email(
                tenant_info["admin_email"],
                tenant_info["admin_username"],
                tenant_info["tenant_name"],
                tenant_info["days_remaining"],
                tenant_info["trial_end_date"]
            )
            
            # リマインダーログを記録
            await self._log_reminder(
                tenant_info["tenant_id"],
                "email",
                str(tenant_info["days_remaining"]),
                message,
                email_sent
            )
            
            return email_sent
            
        except Exception as e:
            logger.error(f"メールリマインダー送信エラー: {str(e)}")
            # エラーログも記録
            await self._log_reminder(
                tenant_info["tenant_id"],
                "email",
                str(tenant_info["days_remaining"]),
                SystemMessages.TRIAL_REMINDER_MESSAGE.format(
                    remaining_days=tenant_info["days_remaining"]
                ),
                False,
                str(e)
            )
            return False
    
    async def _create_dashboard_notification(self, tenant_info: Dict[str, Any]) -> bool:
        """
        ダッシュボード通知を作成
        
        引数:
            tenant_info: テナント情報
        戻り値:
            bool: 作成成功時True
        """
        try:
            # テナントの全ユーザーに通知を作成
            query = select(User).where(User.tenant_id == tenant_info["tenant_id"])
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            notifications_created = 0
            
            for user in users:
                notification = Notification(
                    tenant_id=tenant_info["tenant_id"],
                    user_id=str(user.id),
                    notification_type="trial_reminder",
                    title=f"お試し利用期間終了まで{tenant_info['days_remaining']}日",
                    message=SystemMessages.TRIAL_REMINDER_MESSAGE.format(
                        remaining_days=tenant_info["days_remaining"]
                    ),
                    is_read=False
                )
                
                self.db.add(notification)
                notifications_created += 1
            
            await self.db.commit()
            
            # リマインダーログを記録
            await self._log_reminder(
                tenant_info["tenant_id"],
                "dashboard",
                str(tenant_info["days_remaining"]),
                SystemMessages.TRIAL_REMINDER_MESSAGE.format(
                    remaining_days=tenant_info["days_remaining"]
                ),
                True
            )
            
            return notifications_created > 0
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"ダッシュボード通知作成エラー: {str(e)}")
            return False
    
    async def _log_reminder(
        self, 
        tenant_id: str, 
        reminder_type: str, 
        days_before_expiry: str, 
        message: str, 
        is_sent: bool, 
        error_message: Optional[str] = None
    ) -> None:
        """
        リマインダーログを記録
        
        引数:
            tenant_id: テナントID
            reminder_type: リマインダータイプ
            days_before_expiry: 終了何日前のリマインダーか
            message: 送信メッセージ
            is_sent: 送信成功フラグ
            error_message: エラーメッセージ（オプション）
        """
        try:
            reminder_log = ReminderLog(
                tenant_id=tenant_id,
                reminder_type=reminder_type,
                days_before_expiry=days_before_expiry,
                message=message,
                sent_at=DateTimeUtils.now() if is_sent else None,
                is_sent=is_sent,
                error_message=error_message
            )
            
            self.db.add(reminder_log)
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"リマインダーログ記録エラー: {str(e)}")
    
    async def get_tenant_notifications(
        self, 
        tenant_id: str, 
        user_id: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50
    ) -> List[Notification]:
        """
        テナントの通知一覧を取得
        
        引数:
            tenant_id: テナントID
            user_id: ユーザーID（オプション、指定時はそのユーザーのみ）
            is_read: 既読状態フィルタ（オプション）
            limit: 取得件数上限
        戻り値:
            List[Notification]: 通知一覧
        """
        try:
            query = select(Notification).where(Notification.tenant_id == tenant_id)
            
            if user_id:
                query = query.where(Notification.user_id == user_id)
            
            if is_read is not None:
                # statusベースでフィルタリング（READ = 既読、PENDING = 未読）
                if is_read:
                    query = query.where(Notification.status == "READ")
                else:
                    query = query.where(Notification.status != "READ")
            
            query = query.order_by(Notification.created_at.desc()).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"通知一覧取得エラー: {str(e)}")
            raise
    
    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        通知を既読にする
        
        引数:
            notification_id: 通知ID
            user_id: ユーザーID
        戻り値:
            bool: 更新成功時True
        """
        try:
            query = select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
            
            result = await self.db.execute(query)
            notification = result.scalar_one_or_none()
            
            if not notification:
                return False
            
            notification.is_read = True
            notification.read_at = DateTimeUtils.now()
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"通知既読更新エラー: {str(e)}")
            raise
