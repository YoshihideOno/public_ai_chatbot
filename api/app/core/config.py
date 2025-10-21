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
from typing import List, Optional
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
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "https://your-vercel-app.vercel.app",
    ]
    
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
    
    class Config:
        """
        設定クラスの設定
        
        Pydanticの設定を定義します。
        env_fileで環境変数ファイルを指定し、case_sensitiveで大文字小文字を区別します。
        """
        env_file = ".env"
        case_sensitive = True

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
            if not self.DATABASE_URL:
                raise ValueError("DATABASE_URLが設定されていません")
            
            # CORS設定のチェック
            if not self.BACKEND_CORS_ORIGINS:
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
