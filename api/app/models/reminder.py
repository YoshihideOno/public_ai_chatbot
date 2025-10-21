"""
リマインダー管理モデル

このファイルはリマインダー機能に関するSQLAlchemyモデルを定義します。
お試し利用期間終了前のリマインダー送信履歴を管理します。

主な機能:
- リマインダー送信履歴の管理
- テナント毎のリマインダー状態追跡
- メール・ダッシュボード通知の記録
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ReminderLog(Base):
    """
    リマインダーログモデル
    
    お試し利用期間終了前のリマインダー送信履歴を管理します。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: リマインダーログの一意識別子（UUID）
        tenant_id: 対象テナントID（外部キー）
        reminder_type: リマインダータイプ（email, dashboard）
        days_before_expiry: 終了何日前のリマインダーか
        message: 送信メッセージ
        sent_at: 送信日時
        is_sent: 送信完了フラグ
        error_message: エラーメッセージ（送信失敗時）
        created_at: 作成日時
    """
    __tablename__ = "reminder_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    reminder_type = Column(String(20), nullable=False)  # email, dashboard
    days_before_expiry = Column(String(10), nullable=False)  # 7, 3, 1
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    is_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="reminder_logs")


class Notification(Base):
    """
    通知モデル
    
    ダッシュボード内の通知情報を管理します。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: 通知の一意識別子（UUID）
        tenant_id: 対象テナントID（外部キー）
        user_id: 対象ユーザーID（外部キー、オプション）
        notification_type: 通知タイプ（trial_reminder, trial_expired等）
        title: 通知タイトル
        message: 通知メッセージ
        is_read: 既読フラグ
        read_at: 既読日時
        created_at: 作成日時
    """
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
