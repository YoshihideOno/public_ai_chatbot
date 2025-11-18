"""add_knowledge_registered_at_to_tenants

Revision ID: 4ce9e08004a9
Revises: 0cff6f7b8b54
Create Date: 2025-11-18 17:10:28.982883

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ce9e08004a9'
down_revision = '0cff6f7b8b54'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    tenantsテーブルにknowledge_registered_atカラムを追加します。
    初回ナレッジ登録日時を記録するためのカラムです。
    """
    # テーブルが存在するかチェック
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # テーブルが存在する場合のみ処理
    if 'tenants' not in inspector.get_table_names():
        return
    
    # カラムが存在するかチェック
    columns = [col['name'] for col in inspector.get_columns('tenants')]
    if 'knowledge_registered_at' not in columns:
        op.add_column(
            'tenants',
            sa.Column(
                'knowledge_registered_at',
                sa.DateTime(timezone=True),
                nullable=True
            )
        )


def downgrade() -> None:
    """
    tenantsテーブルからknowledge_registered_atカラムを削除します。
    """
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # テーブルが存在する場合のみ処理
    if 'tenants' not in inspector.get_table_names():
        return
    
    columns = [col['name'] for col in inspector.get_columns('tenants')]
    if 'knowledge_registered_at' in columns:
        op.drop_column('tenants', 'knowledge_registered_at')
