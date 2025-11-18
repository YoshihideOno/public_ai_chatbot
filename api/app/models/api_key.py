"""
APIキー管理モデル

このファイルはテナント毎のAPIキー情報を管理するためのSQLAlchemyモデルを定義します。
LLMプロバイダー毎のAPIキーとモデル設定を管理します。

主な機能:
- APIキー情報の管理
- LLMプロバイダーとモデルの関連付け
- テナント毎の独立したAPIキー設定
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ApiKey(Base):
    """
    APIキーモデル
    
    テナント毎のLLMプロバイダーAPIキー情報を管理します。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: APIキーの一意識別子（UUID）
        tenant_id: 所属テナントID（外部キー）
        provider: LLMプロバイダー名（openai, anthropic, google等）
        api_key: APIキー文字列（暗号化して保存）
        model_name: 使用するLLMモデル名
        is_active: アクティブ状態フラグ
        created_at: 作成日時
        updated_at: 更新日時
    """
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_tenant_id", "tenant_id"),
        Index("ix_api_keys_provider", "provider"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    provider = Column(String(50), nullable=False)
    api_key = Column(String(500), nullable=False)  # 暗号化して保存
    model_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
