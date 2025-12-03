from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from uuid import UUID
import re


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
            raise ValueError('テナント識別子は3文字以上である必要があります')
        if len(v) > 255:
            raise ValueError('テナント識別子は255文字以内である必要があります')
        # 英数字、ハイフン、アンダースコアのみ許可
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('テナント識別子は英数字、ハイフン、アンダースコアのみ使用可能です')
        return v.lower()


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    plan: Optional[TenantPlan] = None
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None
    # ウィジェット設置を許可するオリジン（CSV形式: "https://foo.com,https://bar.com"）
    allowed_widget_origins: Optional[str] = None
    
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
                raise ValueError('テナント識別子は3文字以上である必要があります')
            if len(v) > 255:
                raise ValueError('テナント識別子は255文字以内である必要があります')
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('テナント識別子は英数字、ハイフン、アンダースコアのみ使用可能です')
        return v.lower() if v else v


class TenantInDB(TenantBase):
    id: str
    api_key: str
    # ウィジェット設置を許可するオリジン（CSV形式文字列）
    allowed_widget_origins: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    @validator('id', pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class Tenant(TenantInDB):
    pass


class TenantPublic(TenantBase):
    """
    外部公開用のテナントスキーマ（機微情報を含まない）
    - api_key は含めない
    """
    id: str
    # ウィジェット設置を許可するオリジン（CSV形式文字列）
    allowed_widget_origins: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @validator('id', pre=True)
    def convert_uuid_to_str_public(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True


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
    default_model: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: int = 1024
    chunk_overlap: int = 200
    max_queries_per_day: int = 1000
    max_storage_mb: int = 100
    enable_api_access: bool = True
    enable_webhook: bool = True
    webhook_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500
    
    @validator('default_model')
    def validate_default_model(cls, v):
        # Noneの場合はバリデーションをスキップ（未選択の場合）
        if v is None:
            return v
        # 利用可能なモデル一覧（LLMServiceから取得）
        available_models = [
            "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet",
            "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"
        ]
        if v not in available_models:
            raise ValueError(f'サポートされていないモデル: {v}')
        return v
    
    @validator('embedding_model')
    def validate_embedding_model(cls, v):
        # Noneの場合はバリデーションをスキップ（未選択の場合）
        if v is None:
            return v
        # 利用可能なモデル一覧（LLMServiceから取得）
        available_models = [
            "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini",
            "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3-5-sonnet",
            "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"
        ]
        if v not in available_models:
            raise ValueError(f'サポートされていないモデル: {v}')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if v < 0.0 or v > 2.0:
            raise ValueError('temperatureは0.0-2.0の範囲である必要があります')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v < 1 or v > 4000:
            raise ValueError('max_tokensは1-4000の範囲である必要があります')
        return v
    
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
