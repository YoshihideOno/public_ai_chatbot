"""
テナント管理モデル

このファイルはテナント（顧客企業）の情報を管理するためのSQLAlchemyモデルを定義します。
マルチテナントアーキテクチャにおけるテナント分離の基盤となる重要なモデルです。

主な機能:
- テナント基本情報の管理
- 設定情報の保存
- ユーザーとの関連付け
"""

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Tenant(Base):
    """
    テナント（顧客企業）モデル
    
    マルチテナントアーキテクチャにおけるテナント情報を管理します。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: テナントの一意識別子（UUID）
        name: テナント名
        domain: テナントのドメイン名（ユニーク）
        plan: プラン種別（FREE, BASIC, PRO, ENTERPRISE）
        status: ステータス（ACTIVE, SUSPENDED, DELETED）
        settings: テナント固有の設定（JSON形式）
        knowledge_registered_at: 初回ナレッジ登録日時
        created_at: 作成日時
        updated_at: 更新日時
        deleted_at: 削除日時（ソフトデリート用）
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default="FREE")
    status = Column(String(50), nullable=False, default="ACTIVE")
    api_key = Column(String(255), nullable=False, unique=True)
    settings = Column(JSONB, nullable=False, server_default='{}')
    knowledge_registered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    files = relationship("File", back_populates="tenant")
    api_keys = relationship("ApiKey", back_populates="tenant")
    reminder_logs = relationship("ReminderLog", back_populates="tenant")
    notifications = relationship("Notification", back_populates="tenant")
