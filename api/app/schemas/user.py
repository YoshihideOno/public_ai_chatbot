from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: UserRole = UserRole.OPERATOR


class UserCreate(UserBase):
    password: str
    tenant_id: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        return v
    
    @validator('role', pre=True)
    def validate_role(cls, v):
        if isinstance(v, str):
            try:
                return UserRole(v)
            except ValueError:
                raise ValueError(f'無効なロール: {v}')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None:
            if len(v) < 8:
                raise ValueError('パスワードは8文字以上である必要があります')
            if not any(c.isupper() for c in v):
                raise ValueError('パスワードには大文字を含める必要があります')
            if not any(c.islower() for c in v):
                raise ValueError('パスワードには小文字を含める必要があります')
            if not any(c.isdigit() for c in v):
                raise ValueError('パスワードには数字を含める必要があります')
        return v


class TenantInfo(BaseModel):
    id: str
    name: str
    domain: str
    plan: str
    status: str
    
    class Config:
        from_attributes = True


class UserInDB(UserBase):
    id: str
    tenant_id: Optional[str]
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    tenant: Optional[TenantInfo] = None

    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    @validator('tenant_id', pre=True)
    def convert_tenant_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('パスワードは8文字以上である必要があります')
        if not any(c.isupper() for c in v):
            raise ValueError('パスワードには大文字を含める必要があります')
        if not any(c.islower() for c in v):
            raise ValueError('パスワードには小文字を含める必要があります')
        if not any(c.isdigit() for c in v):
            raise ValueError('パスワードには数字を含める必要があります')
        return v
