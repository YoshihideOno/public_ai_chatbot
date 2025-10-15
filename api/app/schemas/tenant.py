from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TenantPlan(str, Enum):
    FREE = "FREE"
    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class TenantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class TenantBase(BaseModel):
    name: str
    domain: str
    plan: TenantPlan = TenantPlan.FREE
    status: TenantStatus = TenantStatus.ACTIVE
    settings: Dict[str, Any] = {}
    
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 2:
            raise ValueError('テナント名は2文字以上である必要があります')
        if len(v) > 255:
            raise ValueError('テナント名は255文字以内である必要があります')
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        if not v or len(v) < 3:
            raise ValueError('ドメインは3文字以上である必要があります')
        if len(v) > 255:
            raise ValueError('ドメインは255文字以内である必要があります')
        # 基本的なドメイン形式チェック
        if '.' not in v or v.startswith('.') or v.endswith('.'):
            raise ValueError('有効なドメイン形式を入力してください')
        return v.lower()


class TenantCreate(TenantBase):
    admin_user: Optional[Dict[str, Any]] = None
    
    @validator('admin_user')
    def validate_admin_user(cls, v):
        if v is not None:
            required_fields = ['email', 'username', 'password']
            for field in required_fields:
                if field not in v:
                    raise ValueError(f'管理者ユーザーの{field}は必須です')
        return v


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    plan: Optional[TenantPlan] = None
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v) < 2:
                raise ValueError('テナント名は2文字以上である必要があります')
            if len(v) > 255:
                raise ValueError('テナント名は255文字以内である必要があります')
        return v
    
    @validator('domain')
    def validate_domain(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('ドメインは3文字以上である必要があります')
            if len(v) > 255:
                raise ValueError('ドメインは255文字以内である必要があります')
            if '.' not in v or v.startswith('.') or v.endswith('.'):
                raise ValueError('有効なドメイン形式を入力してください')
        return v.lower() if v else v


class TenantInDB(TenantBase):
    id: str
    api_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Tenant(TenantInDB):
    pass


class TenantWithUsers(Tenant):
    users: List[Dict[str, Any]] = []
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    total_users: int
    active_users: int
    total_files: int
    total_chunks: int
    total_conversations: int
    storage_used_mb: float
    queries_this_month: int
    last_activity: Optional[datetime] = None


class TenantSettings(BaseModel):
    default_model: str = "gpt-4"
    chunk_size: int = 1024
    chunk_overlap: int = 200
    max_queries_per_day: int = 1000
    max_storage_mb: int = 100
    enable_api_access: bool = True
    enable_webhook: bool = False
    webhook_url: Optional[str] = None
    
    @validator('chunk_size')
    def validate_chunk_size(cls, v):
        if v < 256 or v > 4096:
            raise ValueError('チャンクサイズは256-4096の範囲である必要があります')
        return v
    
    @validator('chunk_overlap')
    def validate_chunk_overlap(cls, v):
        if v < 0 or v > 512:
            raise ValueError('チャンクオーバーラップは0-512の範囲である必要があります')
        return v
    
    @validator('max_queries_per_day')
    def validate_max_queries(cls, v):
        if v < 0:
            raise ValueError('最大質問数は0以上である必要があります')
        return v
    
    @validator('max_storage_mb')
    def validate_max_storage(cls, v):
        if v < 0:
            raise ValueError('最大ストレージサイズは0以上である必要があります')
        return v


class TenantApiKey(BaseModel):
    api_key: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True


class TenantEmbedSnippet(BaseModel):
    snippet: str
    tenant_id: str
    api_key: str
    
    class Config:
        from_attributes = True
