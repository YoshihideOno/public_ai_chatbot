"""
確認トークンモデル

このファイルはメール確認用のトークンを管理するためのSQLAlchemyモデルを定義します。
ユーザー登録時のメール確認機能を提供します。

主な機能:
- 確認トークンの生成・管理
- トークンの有効期限管理
- トークンの使用状態管理
"""

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, timedelta


class VerificationToken(Base):
    """
    確認トークンモデル
    
    メール確認用のトークン情報を管理するモデルです。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: トークンの一意識別子（UUID）
        user_id: 関連するユーザーID（外部キー）
        token: 確認用トークン（ハッシュ化済み）
        token_type: トークンの種類（email_verification, password_reset等）
        expires_at: トークンの有効期限
        is_used: トークンの使用済みフラグ
        created_at: 作成日時
        updated_at: 更新日時
    """
    __tablename__ = "verification_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), nullable=False, index=True)
    token_type = Column(String(50), nullable=False, default="email_verification")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="verification_tokens")
