"""
APIキー管理スキーマ

このファイルはAPIキー管理に使用されるPydanticスキーマを定義します。
LLMプロバイダー毎のAPIキー登録・更新・取得機能をサポートします。

主な機能:
- APIキー登録データのバリデーション
- APIキー情報のレスポンス形式
- プロバイダー・モデル選択のサポート
"""

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.core.constants import ApiKeySettings


class ApiKeyCreate(BaseModel):
    """
    APIキー作成データ
    
    LLMプロバイダーのAPIキーを登録するためのスキーマです。
    
    属性:
        provider: LLMプロバイダー名
        api_key: APIキー文字列
        model: 使用するLLMモデル名
    """
    provider: str
    api_key: str
    model: str
    
    @validator('provider')
    def validate_provider(cls, v):
        """プロバイダーのバリデーション"""
        if not ApiKeySettings.is_provider_supported(v):
            raise ValueError(f'サポートされていないプロバイダー: {v}')
        return v
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """APIキーのバリデーション"""
        if not v or len(v.strip()) < 10:
            raise ValueError('APIキーは10文字以上である必要があります')
        if len(v) > 500:
            raise ValueError('APIキーは500文字以内である必要があります')
        return v.strip()
    
    @validator('model')
    def validate_model(cls, v, values):
        """モデルのバリデーション"""
        provider = values.get('provider')
        if provider and not ApiKeySettings.is_provider_supported(provider):
            return v
        
        supported_models = ApiKeySettings.get_supported_models(provider)
        if supported_models and v not in supported_models:
            raise ValueError(f'プロバイダー {provider} でサポートされていないモデル: {v}')
        return v


class ApiKeyUpdate(BaseModel):
    """
    APIキー更新データ
    
    APIキー情報を更新するためのスキーマです。
    
    属性:
        api_key: 新しいAPIキー文字列（オプション）
        model: 新しいモデル名（オプション）
        is_active: アクティブ状態（オプション）
    """
    api_key: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """APIキーのバリデーション"""
        if v is not None:
            if not v or len(v.strip()) < 10:
                raise ValueError('APIキーは10文字以上である必要があります')
            if len(v) > 500:
                raise ValueError('APIキーは500文字以内である必要があります')
            return v.strip()
        return v


class ApiKeyResponse(BaseModel):
    """
    APIキーレスポンスデータ
    
    APIキー情報を返すためのスキーマです。
    セキュリティのため、APIキーは部分的にマスクして返します。
    
    属性:
        id: APIキーID
        tenant_id: 所属テナントID
        provider: LLMプロバイダー名
        api_key_masked: マスクされたAPIキー
        model: 使用するLLMモデル名
        is_active: アクティブ状態
        created_at: 作成日時
        updated_at: 更新日時
    """
    id: str
    tenant_id: str
    provider: str
    api_key_masked: str
    model: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    @classmethod
    def mask_api_key(cls, api_key: str) -> str:
        """
        APIキーをマスクする
        
        引数:
            api_key: 元のAPIキー
        戻り値:
            str: マスクされたAPIキー
        """
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]


class ApiKeyListResponse(BaseModel):
    """
    APIキー一覧レスポンスデータ
    
    テナントのAPIキー一覧を返すためのスキーマです。
    
    属性:
        api_keys: APIキー一覧
        total_count: 総数
    """
    api_keys: List[ApiKeyResponse]
    total_count: int


class ProviderModelInfo(BaseModel):
    """
    プロバイダー・モデル情報
    
    利用可能なプロバイダーとモデルの情報を返すためのスキーマです。
    
    属性:
        provider: プロバイダー名
        models: 利用可能なモデル一覧
    """
    provider: str
    models: List[str]


class ProviderModelListResponse(BaseModel):
    """
    プロバイダー・モデル一覧レスポンスデータ
    
    利用可能なプロバイダーとモデルの一覧を返すためのスキーマです。
    
    属性:
        providers: プロバイダー・モデル情報一覧
    """
    providers: List[ProviderModelInfo]
