from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'app'))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Alembicは同期処理のため、database.pyのエンジン作成をスキップする
# database.pyをインポートする前に環境変数を設定
os.environ["ALEMBIC_MIGRATION"] = "true"

from app.core.database import Base  # noqa: E402
from app import models  # noqa: F401,E402

target_metadata = Base.metadata

def _resolve_sync_db_url() -> str:
    """
    同期処理用のデータベースURLを解決する
    
    asyncpg用URLをpsycopg2用に変換し、SSLパラメータも適切に変換します。
    """
    url = (
        os.getenv("DATABASE_URL_SYNC")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
    )
    if not url:
        raise RuntimeError("DATABASE_URL_SYNC も DATABASE_URL も設定されていません")
    
    # asyncpg用URLをpsycopg2用に変換
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    
    # URLをパースして、SSLパラメータを変換
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # ssl=true を sslmode=require に変換（psycopg2は ssl=true を理解しない）
    if 'ssl' in query_params and query_params['ssl'] == ['true']:
        del query_params['ssl']
        if 'sslmode' not in query_params:
            query_params['sslmode'] = ['require']
    
    # クエリパラメータを再構築
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    url = urlunparse(new_parsed)
    
    return url


def run_migrations_offline():
    url = _resolve_sync_db_url()
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    url = _resolve_sync_db_url()
    
    # 同期エンジンを作成
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
