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
import os

# Alembic実行時はエンジンを作成しない（Alembicは同期処理のため）
# Create async engine with optimized pool settings
if not os.getenv("ALEMBIC_MIGRATION"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        poolclass=NullPool,  # 非同期エンジンではNullPoolを使用
        connect_args={
            "command_timeout": 30,  # コマンドタイムアウト（30秒）
            "server_settings": {
                "application_name": "ai_chatbot_api",
                "lock_timeout": "30s",  # ロックタイムアウト（30秒）
                "statement_timeout": "60s",  # ステートメントタイムアウト（60秒）
                "timezone": "Asia/Tokyo",  # タイムゾーン設定
            }
        }
    )
else:
    # Alembic実行時はダミーエンジン（実際には使用されない）
    engine = None

# Create async session factory
if engine is not None:
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    # Alembic実行時はダミーセッションファクトリ
    AsyncSessionLocal = None

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
    if AsyncSessionLocal is None:
        raise RuntimeError("データベースエンジンが初期化されていません")
    async with AsyncSessionLocal() as session:
        try:
            # NullPoolの場合は接続プール情報をスキップ
            if engine is not None and hasattr(engine.pool, 'size'):
                pool = engine.pool
                logging.info(f"DB接続プール状態: size={pool.size()}, checked_in={pool.checkedin()}, checked_out={pool.checkedout()}, overflow={pool.overflow()}")
            else:
                logging.info("DB接続: NullPool使用中")
            
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
    if engine is None:
        raise RuntimeError("データベースエンジンが初期化されていません")
    try:
        async with engine.begin() as conn:
            # Import all models here to ensure they are registered
            import app.models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
            logging.info("データベーステーブルの初期化が完了しました")
    except Exception as e:
        logging.error(f"データベース初期化エラー: {str(e)}")
        raise
