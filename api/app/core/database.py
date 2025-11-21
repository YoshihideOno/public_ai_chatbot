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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import logging
import os


def _normalize_async_db_url(url: str) -> str:
    """
    asyncpg用のデータベースURLを正規化する
    
    asyncpgは`sslmode`パラメータを理解しないため、`sslmode=require`を`ssl=true`に変換します。
    また、`postgresql://`形式のURLを`postgresql+asyncpg://`に変換します。
    
    引数:
        url: データベース接続URL
        
    戻り値:
        str: 正規化されたURL
    """
    if not url:
        return url
    
    # postgresql:// を postgresql+asyncpg:// に変換（未設定の場合）
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # URLをパースして、SSLパラメータを変換
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # デバッグ: パース前のクエリパラメータを確認
    if 'sslmode' in query_params or 'channel_binding' in query_params:
        print(f"[DB DEBUG] URL正規化前のクエリパラメータ: sslmode={query_params.get('sslmode')}, channel_binding={query_params.get('channel_binding')}, ssl={query_params.get('ssl')}", flush=True)
        logging.warning(f"URL正規化前のクエリパラメータ: sslmode={query_params.get('sslmode')}, channel_binding={query_params.get('channel_binding')}, ssl={query_params.get('ssl')}")
    
    # sslmode=require を ssl=true に変換（asyncpgは sslmode を理解しない）
    if 'sslmode' in query_params:
        sslmode_value = query_params['sslmode'][0] if query_params['sslmode'] else None
        del query_params['sslmode']
        # sslmodeがrequire, verify-ca, verify-fullの場合はssl=trueに変換
        if sslmode_value in ['require', 'verify-ca', 'verify-full']:
            if 'ssl' not in query_params:
                query_params['ssl'] = ['true']
        elif sslmode_value == 'disable':
            if 'ssl' not in query_params:
                query_params['ssl'] = ['false']
        # allow, preferの場合はssl=trueに変換（安全のため）
        elif sslmode_value in ['allow', 'prefer']:
            if 'ssl' not in query_params:
                query_params['ssl'] = ['true']
        # sslmodeが空文字列や無効な値の場合はssl=trueに変換（安全のため）
        elif not sslmode_value or sslmode_value not in ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']:
            logging.warning(f"無効なsslmode値 '{sslmode_value}' を検出しました。ssl=trueに変換します。")
            if 'ssl' not in query_params:
                query_params['ssl'] = ['true']
    
    # channel_bindingパラメータはasyncpgでは無視されるが、削除しておく
    if 'channel_binding' in query_params:
        del query_params['channel_binding']
    
    # クエリパラメータを再構築
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    url = urlunparse(new_parsed)
    
    # デバッグ: 正規化後のURLにsslmodeが含まれていないか確認
    if 'sslmode' in url.lower():
        print(f"[DB DEBUG] 警告: 正規化後のURLにsslmodeが含まれています: {url}", flush=True)
        logging.error(f"警告: 正規化後のURLにsslmodeが含まれています: {url}")
        # 再度パースして確認
        re_parsed = urlparse(url)
        re_query_params = parse_qs(re_parsed.query)
        if 'sslmode' in re_query_params:
            print(f"[DB DEBUG] 再パース後のクエリパラメータにsslmodeが含まれています: {re_query_params.get('sslmode')}", flush=True)
            logging.error(f"再パース後のクエリパラメータにsslmodeが含まれています: {re_query_params.get('sslmode')}")
            # 強制的に削除
            del re_query_params['sslmode']
            new_query = urlencode(re_query_params, doseq=True)
            new_parsed = re_parsed._replace(query=new_query)
            url = urlunparse(new_parsed)
            print(f"[DB DEBUG] sslmodeを強制的に削除しました: {url}", flush=True)
            logging.warning(f"sslmodeを強制的に削除しました: {url}")
    
    # 最終確認: 正規化後のURLにsslmodeが含まれていないか確認
    final_parsed = urlparse(url)
    final_query_params = parse_qs(final_parsed.query)
    if 'sslmode' in final_query_params:
        print(f"[DB DEBUG] エラー: 最終確認でsslmodeが検出されました: {final_query_params.get('sslmode')}", flush=True)
        logging.error(f"エラー: 最終確認でsslmodeが検出されました: {final_query_params.get('sslmode')}")
    
    return url


# Alembic実行時はエンジンを作成しない（Alembicは同期処理のため）
# Create async engine with optimized pool settings
if not os.getenv("ALEMBIC_MIGRATION"):
    async_db_url = settings.ASYNC_DATABASE_URL or settings.DATABASE_URL
    if not async_db_url:
        raise RuntimeError("ASYNC_DATABASE_URLまたはDATABASE_URLが設定されていません")
    
    # デバッグ用: 正規化前のURLをログ出力（パスワード部分はマスク）
    original_url_for_log = async_db_url
    if '@' in original_url_for_log:
        # パスワード部分をマスク
        parts = original_url_for_log.split('@')
        if len(parts) == 2:
            auth_part = parts[0]
            if ':' in auth_part:
                user_pass = auth_part.split(':', 1)
                if len(user_pass) == 2:
                    original_url_for_log = f"{user_pass[0]}:****@{parts[1]}"
    print(f"[DB DEBUG] 正規化前のDB URL: {original_url_for_log}", flush=True)
    logging.info(f"正規化前のDB URL: {original_url_for_log}")
    
    # sslmodeが含まれていないか確認（正規化前）
    if 'sslmode' in async_db_url.lower():
        print(f"[DB DEBUG] 警告: 正規化前のURLにsslmodeが含まれています: {original_url_for_log}", flush=True)
        logging.warning(f"正規化前のURLにsslmodeが含まれています: {original_url_for_log}")
    
    # asyncpg用にURLを正規化（sslmodeをsslに変換）
    async_db_url_normalized = _normalize_async_db_url(async_db_url)
    
    # デバッグ用: 正規化後のURLをログ出力（パスワード部分はマスク）
    normalized_url_for_log = async_db_url_normalized
    if '@' in normalized_url_for_log:
        # パスワード部分をマスク
        parts = normalized_url_for_log.split('@')
        if len(parts) == 2:
            auth_part = parts[0]
            if ':' in auth_part:
                user_pass = auth_part.split(':', 1)
                if len(user_pass) == 2:
                    normalized_url_for_log = f"{user_pass[0]}:****@{parts[1]}"
    print(f"[DB DEBUG] 正規化後のDB URL: {normalized_url_for_log}", flush=True)
    logging.info(f"正規化後のDB URL: {normalized_url_for_log}")
    
    # sslmodeが含まれていないか確認（正規化後）
    if 'sslmode' in async_db_url_normalized.lower():
        print(f"[DB DEBUG] エラー: 正規化後のURLにsslmodeが含まれています: {normalized_url_for_log}", flush=True)
        logging.error(f"警告: 正規化後のURLにsslmodeが含まれています: {normalized_url_for_log}")
        # 強制的に削除を試みる
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(async_db_url_normalized)
        query_params = parse_qs(parsed.query)
        if 'sslmode' in query_params:
            del query_params['sslmode']
            new_query = urlencode(query_params, doseq=True)
            new_parsed = parsed._replace(query=new_query)
            async_db_url_normalized = urlunparse(new_parsed)
            print(f"[DB DEBUG] sslmodeを強制的に削除しました: {normalized_url_for_log}", flush=True)
            logging.warning(f"sslmodeを強制的に削除しました")
    
    async_db_url = async_db_url_normalized
    
    # 最終確認: create_async_engineに渡される直前のURLを確認
    final_check_parsed = urlparse(async_db_url)
    final_check_query_params = parse_qs(final_check_parsed.query)
    print(f"[DB DEBUG] create_async_engineに渡されるURLのクエリパラメータ: {final_check_query_params}", flush=True)
    
    # sslパラメータをconnect_argsに移動（URLから削除）
    # asyncpgはURLクエリパラメータのssl=trueを正しく処理できない場合があるため、
    # connect_argsで明示的に設定する
    ssl_enabled = False
    if 'ssl' in final_check_query_params:
        ssl_value = final_check_query_params['ssl'][0] if final_check_query_params['ssl'] else None
        if ssl_value and ssl_value.lower() in ['true', '1', 'yes']:
            ssl_enabled = True
        del final_check_query_params['ssl']
    
    # sslmodeが含まれている場合は削除
    if 'sslmode' in final_check_query_params:
        print(f"[DB DEBUG] エラー: create_async_engineに渡されるURLにsslmodeが含まれています: {final_check_query_params.get('sslmode')}", flush=True)
        logging.error(f"エラー: create_async_engineに渡されるURLにsslmodeが含まれています: {final_check_query_params.get('sslmode')}")
        del final_check_query_params['sslmode']
    
    # channel_bindingが含まれている場合は削除（asyncpgでは使用されない）
    if 'channel_binding' in final_check_query_params:
        del final_check_query_params['channel_binding']
    
    # クエリパラメータを再構築（ssl, sslmode, channel_bindingを削除したURL）
    new_query = urlencode(final_check_query_params, doseq=True)
    new_parsed = final_check_parsed._replace(query=new_query)
    async_db_url_clean = urlunparse(new_parsed)
    
    print(f"[DB DEBUG] クリーンアップ後のURL: {async_db_url_clean}", flush=True)
    print(f"[DB DEBUG] SSL設定: {ssl_enabled}", flush=True)

    engine = create_async_engine(
        async_db_url_clean,
        echo=settings.DEBUG,
        future=True,
        poolclass=NullPool,  # 非同期エンジンではNullPoolを使用
        connect_args={
            "command_timeout": 30,  # コマンドタイムアウト（30秒）
            "ssl": ssl_enabled,  # SSL接続を明示的に設定
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
