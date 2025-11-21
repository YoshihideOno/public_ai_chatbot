"""
アプリケーション設定管理

このファイルはアプリケーション全体の設定を管理するためのモジュールです。
Pydantic Settingsを使用して環境変数から設定値を読み込み、型安全な設定管理を提供します。

主な機能:
- 環境変数からの設定値読み込み
- データベース接続設定
- セキュリティ設定（JWT、CORS）
- AI API設定
- 環境別設定管理
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os
import logging


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    
    Pydantic BaseSettingsを継承し、環境変数から設定値を読み込みます。
    型安全な設定管理とバリデーション機能を提供します。
    
    属性:
        PROJECT_NAME: プロジェクト名
        VERSION: アプリケーションバージョン
        API_V1_STR: APIバージョン文字列
        DATABASE_URL: データベース接続URL
        BACKEND_CORS_ORIGINS: CORS許可オリジン
        SECRET_KEY: JWT署名用秘密鍵
        ALGORITHM: JWT署名アルゴリズム
        ACCESS_TOKEN_EXPIRE_MINUTES: アクセストークン有効期限（分）
        REFRESH_TOKEN_EXPIRE_DAYS: リフレッシュトークン有効期限（日）
        OPENAI_API_KEY: OpenAI APIキー
        ANTHROPIC_API_KEY: Anthropic APIキー
        ENVIRONMENT: 実行環境
        DEBUG: デバッグモード
        TIMEZONE: アプリケーションタイムゾーン
    """
    PROJECT_NAME: str = "AI Chatbot API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@db:5432/ai_chatbot_db"
    ASYNC_DATABASE_URL: Optional[str] = None
    DATABASE_URL_SYNC: Optional[str] = None
    
    # CORS
    # 環境変数から読み込む際は、カンマ区切りの文字列として扱う
    # Pydantic SettingsがJSONとして解析しようとするのを防ぐため、
    # 型をUnion[str, List[str]]にして、バリデーターでリストに変換する
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://your-vercel-app.vercel.app",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str], None]) -> Union[str, List[str]]:
        """
        CORSオリジンをパース
        
        環境変数からカンマ区切りの文字列として読み込まれた場合、
        そのまま文字列として保持します（後でプロパティでリストに変換）。
        JSONとして解析しようとした場合は、そのまま返します。
        
        引数:
            v: 環境変数の値（文字列、リスト、またはNone）
            
        戻り値:
            Union[str, List[str]]: CORSオリジン（文字列またはリスト）
        """
        if v is None:
            return []
        if isinstance(v, str):
            # 文字列の場合はそのまま返す（JSONとして解析されていない）
            return v
        elif isinstance(v, list):
            # 既にリストの場合はそのまま返す
            return v
        else:
            # その他の場合は空リストを返す
            return []
    
    def get_cors_origins(self) -> List[str]:
        """
        CORSオリジンのリストを返す
        
        戻り値:
            List[str]: CORSオリジンのリスト
        """
        if isinstance(self.BACKEND_CORS_ORIGINS, list):
            return self.BACKEND_CORS_ORIGINS
        elif isinstance(self.BACKEND_CORS_ORIGINS, str):
            if not self.BACKEND_CORS_ORIGINS.strip():
                return []
            return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
        else:
            return []
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None

    # Billing / External Integrations
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_BASIC_MONTHLY: Optional[str] = None
    STRIPE_PRICE_BASIC_YEARLY: Optional[str] = None
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = None
    STRIPE_PRICE_PRO_YEARLY: Optional[str] = None
    RESEND_API_KEY: Optional[str] = None
    EMAIL_FROM_ADDRESS: str = "noreply@synergysoft.jp"  # 本番環境用ドメイン
    
    APP_URL: Optional[str] = None
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Timezone
    TIMEZONE: str = "Asia/Tokyo"
    
    # Storage
    STORAGE_LOCAL_PATH: str = "/tmp/rag_storage"
    BLOB_READ_WRITE_TOKEN: Optional[str] = None
    
    class Config:
        """
        設定クラスの設定
        
        Pydanticの設定を定義します。
        env_fileで環境変数ファイルを指定し、case_sensitiveで大文字小文字を区別します。
        extra = "ignore"で未定義の環境変数を無視します。
        """
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 未定義の環境変数を無視

    def validate_settings(self) -> bool:
        """
        設定値のバリデーション
        
        戻り値:
            bool: バリデーション成功時True、失敗時False
            
        例外:
            ValueError: 無効な設定値
        """
        try:
            # 必須設定のチェック
            if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-change-in-production":
                if self.ENVIRONMENT == "production":
                    raise ValueError("本番環境ではSECRET_KEYを設定してください")
                logging.warning("デフォルトのSECRET_KEYが使用されています")
            
            # データベースURLのチェック
            effective_async_url = self.ASYNC_DATABASE_URL or self.DATABASE_URL
            if not effective_async_url:
                raise ValueError("ASYNC_DATABASE_URLまたはDATABASE_URLが設定されていません")

            effective_sync_url = self.DATABASE_URL_SYNC or self.DATABASE_URL
            if not effective_sync_url:
                raise ValueError("DATABASE_URL_SYNCまたはDATABASE_URLが設定されていません")
            if effective_sync_url.startswith("postgresql+asyncpg://"):
                logging.warning("DATABASE_URL_SYNC に asyncpg 用URLが設定されています。postgresql:// 形式を推奨します。")
            
            # CORS設定のチェック
            cors_origins = self.get_cors_origins()
            if not cors_origins:
                logging.warning("CORS設定が空です")

            # Stripe/Resendの本番必須設定
            if self.ENVIRONMENT == "production":
                if not self.STRIPE_SECRET_KEY:
                    raise ValueError("STRIPE_SECRET_KEYが設定されていません")
                if not self.STRIPE_WEBHOOK_SECRET:
                    raise ValueError("STRIPE_WEBHOOK_SECRETが設定されていません")
                if not self.APP_URL:
                    raise ValueError("APP_URLが設定されていません")
            
            logging.info(f"設定バリデーション完了: {self.ENVIRONMENT}環境")
            return True
            
        except Exception as e:
            logging.error(f"設定バリデーションエラー: {str(e)}")
            raise


# グローバル設定インスタンス
settings = Settings()

# 起動時の設定バリデーション
try:
    settings.validate_settings()
except Exception as e:
    logging.error(f"設定初期化エラー: {str(e)}")
    raise
