"""
データベース接続管理

このファイルはデータベース接続の設定と管理を行うためのモジュールです。
SQLAlchemyの非同期エンジン、セッションファクトリ、ベースモデルクラスの
作成と管理を担当します。

主な機能:
- 非同期データベースエンジンの作成
- セッションファクトリの設定
- ベースモデルクラスの定義
- データベースセッションの依存性注入
- データベース初期化処理
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    poolclass=NullPool,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    データベースセッションの依存性注入関数
    
    この関数はFastAPIの依存性注入システムで使用され、
    各リクエストに対してデータベースセッションを提供します。
    セッションは自動的にクリーンアップされます。
    
    戻り値:
        AsyncSession: データベースセッション
        
    例外:
        SQLAlchemyError: データベース接続エラー
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logging.error(f"データベースセッションエラー: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    データベーステーブルの初期化
    
    この関数はアプリケーション起動時にデータベーステーブルを
    作成します。全てのモデルをインポートしてメタデータを
    登録してからテーブルを作成します。
    
    例外:
        SQLAlchemyError: テーブル作成エラー
    """
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            from app.models import user, chat, tenant, file, chunk  # noqa
            await conn.run_sync(Base.metadata.create_all)
            logging.info("データベーステーブルの初期化が完了しました")
    except Exception as e:
        logging.error(f"データベース初期化エラー: {str(e)}")
        raise
