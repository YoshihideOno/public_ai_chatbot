"""
テナント登録スキーマ

このファイルはテナント登録時に使用されるPydanticスキーマを定義します。
テナント作成とテナント管理者ユーザー作成を同時に行うためのスキーマです。

主な機能:
- テナント登録データのバリデーション
- テナント管理者ユーザー情報のバリデーション
- 統合的な登録フローのサポート
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from app.models.user import UserRole
import re


class TenantRegistrationData(BaseModel):
    """
    テナント登録データ
    
    テナント作成とテナント管理者ユーザー作成を同時に行うためのスキーマです。
    
    属性:
        tenant_name: テナント名
        tenant_domain: テナントドメイン
        admin_email: テナント管理者のメールアドレス
        admin_username: テナント管理者のユーザー名
        admin_password: テナント管理者のパスワード
    """
    tenant_name: str
    tenant_domain: str
    admin_email: EmailStr
    admin_username: str
    admin_password: str
    
    @validator('tenant_name')
    def validate_tenant_name(cls, v):
        """テナント名のバリデーション"""
        if not v or len(v.strip()) < 2:
            raise ValueError('テナント名は2文字以上である必要があります')
        if len(v) > 255:
            raise ValueError('テナント名は255文字以内である必要があります')
        return v.strip()
    
    @validator('tenant_domain')
    def validate_tenant_domain(cls, v):
        """テナント識別子のバリデーション"""
        if not v or len(v.strip()) < 3:
            raise ValueError('テナント識別子は3文字以上である必要があります')
        if len(v) > 255:
            raise ValueError('テナント識別子は255文字以内である必要があります')
        # 英数字、ハイフン、アンダースコアのみ許可
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError('テナント識別子は英数字、ハイフン、アンダースコアのみ使用可能です')
        return v.strip().lower()
    
    @validator('admin_username')
    def validate_admin_username(cls, v):
        """管理者ユーザー名のバリデーション"""
        if not v or len(v.strip()) < 3:
            raise ValueError('ユーザー名は3文字以上である必要があります')
        if len(v) > 100:
            raise ValueError('ユーザー名は100文字以内である必要があります')
        # 英数字とアンダースコアのみ許可
        if not v.replace('_', '').isalnum():
            raise ValueError('ユーザー名は英数字とアンダースコアのみ使用可能です')
        return v.strip()
    
    @validator('admin_password')
    def validate_admin_password(cls, v):
        """管理者パスワードのバリデーション"""
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        return v


class TenantRegistrationResponse(BaseModel):
    """
    テナント登録レスポンス
    
    テナント登録完了後のレスポンスデータです。
    
    属性:
        tenant_id: 作成されたテナントID
        tenant_name: テナント名
        admin_user_id: 作成されたテナント管理者のユーザーID
        admin_email: テナント管理者のメールアドレス
        message: 登録完了メッセージ
    """
    tenant_id: str
    tenant_name: str
    admin_user_id: str
    admin_email: str
    message: str
