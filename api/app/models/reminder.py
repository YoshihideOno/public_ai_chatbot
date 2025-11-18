"""
リマインダー管理モデル

このファイルはリマインダー機能に関するSQLAlchemyモデルを定義します。
お試し利用期間終了前のリマインダー送信履歴を管理します。

主な機能:
- リマインダー送信履歴の管理
- テナント毎のリマインダー状態追跡
- メール・ダッシュボード通知の記録
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Index
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
        sent_at: 送信日時
        is_sent: 送信完了フラグ
        error_message: エラーメッセージ（送信失敗時）
        created_at: 作成日時
        send_date: 送信予定日時
        failure_reason: 失敗理由
    """
    __tablename__ = "reminder_logs"
    __table_args__ = (
        Index("ix_reminder_logs_tenant_id", "tenant_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    reminder_type = Column(String(20), nullable=False)  # email, dashboard
    days_before_expiry = Column(String(10), nullable=True)  # 7, 3, 1
    sent_at = Column(DateTime(timezone=True), nullable=True)
    is_sent = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    send_date = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    
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
        status: 通知ステータス（PENDING, READ等）
        read_at: 既読日時
        created_at: 作成日時
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_tenant_id", "tenant_id"),
        Index("ix_notifications_user_id", "user_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), nullable=True, server_default="PENDING")
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="notifications")
    user = relationship("User", back_populates="notifications")
    
    @property
    def is_read(self) -> bool:
        """
        既読フラグ（statusベース）
        
        戻り値:
            bool: 既読の場合True
        """
        return self.status == "READ"
    
    @is_read.setter
    def is_read(self, value: bool) -> None:
        """
        既読フラグ設定（statusベース）
        
        引数:
            value: 既読フラグ
        """
        if value:
            self.status = "READ"
        else:
            self.status = "PENDING"
