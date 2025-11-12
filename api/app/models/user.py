"""
ユーザーモデル

このファイルはユーザー情報を管理するためのSQLAlchemyモデルを定義します。
ユーザーの基本情報、認証情報、権限管理などの機能を提供します。

主な機能:
- ユーザー基本情報の管理
- ロールベースアクセス制御（RBAC）
- テナントとの関連付け
- 認証状態の管理
- アクティブ・非アクティブ状態の管理
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """
    ユーザーロール列挙型
    
    システム内で使用されるユーザーロールを定義します。
    各ロールには異なる権限レベルが設定されています。
    
    値:
        PLATFORM_ADMIN: プラットフォーム管理者（最高権限）
        TENANT_ADMIN: テナント管理者（テナント内最高権限）
        OPERATOR: 運用者（一般的な操作権限）
        AUDITOR: 監査者（読み取り専用権限）
    """
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    OPERATOR = "OPERATOR"
    AUDITOR = "AUDITOR"


class User(Base):
    """
    ユーザーモデル
    
    システムのユーザー情報を管理するモデルです。
    Baseクラスを継承し、SQLAlchemyのORM機能を利用します。
    
    属性:
        id: ユーザーの一意識別子（整数）
        email: メールアドレス（ユニーク、インデックス付き）
        username: ユーザー名（ユニーク、インデックス付き）
        hashed_password: ハッシュ化されたパスワード
        role: ユーザーロール（RBAC用）
        tenant_id: 所属テナントID（外部キー）
        is_active: アクティブ状態フラグ
        is_verified: メール認証済みフラグ
        last_login_at: 最終ログイン日時
        created_at: 作成日時
        updated_at: 更新日時
        deleted_at: 論理削除日時（NULLの場合は削除されていない）
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, server_default=func.gen_random_uuid())
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user")
