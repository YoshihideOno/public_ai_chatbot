"""
テナント管理モデル

このファイルはテナント（顧客企業）の情報を管理するためのSQLAlchemyモデルを定義します。
マルチテナントアーキテクチャにおけるテナント分離の基盤となる重要なモデルです。

主な機能:
- テナント基本情報の管理
- APIキー管理
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
        api_key: APIアクセス用キー（ユニーク）
        settings: テナント固有の設定（JSON形式）
        created_at: 作成日時
        updated_at: 更新日時
        deleted_at: 削除日時（ソフトデリート用）
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default="FREE")
    status = Column(String(50), nullable=False, default="ACTIVE")
    api_key = Column(String(255), nullable=False, unique=True)
    settings = Column(JSONB, nullable=False, server_default='{}')
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.current_timestamp())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.current_timestamp())
    deleted_at = Column(DateTime(timezone=False), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    files = relationship("File", back_populates="tenant")
