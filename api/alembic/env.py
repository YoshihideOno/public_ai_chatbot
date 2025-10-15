from __future__ import annotations
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'app'))

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.database import Base  # noqa: E402
from app import models  # noqa: F401,E402

target_metadata = Base.metadata

def run_migrations_offline():
    # 環境変数からDATABASE_URLを取得、なければalembic.iniから取得
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # 環境変数からDATABASE_URLを取得、なければalembic.iniから取得
    url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    
    # 設定を更新
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
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
