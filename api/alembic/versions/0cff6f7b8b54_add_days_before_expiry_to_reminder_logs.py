"""add_days_before_expiry_to_reminder_logs

Revision ID: 0cff6f7b8b54
Revises: 2338dfdf8067
Create Date: 2025-11-15 23:00:07.668567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cff6f7b8b54'
down_revision = '2338dfdf8067'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    reminder_logsテーブルにdays_before_expiryカラムを追加します。
    """
    # カラムが存在するかチェック
    from sqlalchemy import inspect, text
    connection = op.get_bind()
    inspector = inspect(connection)
    
    columns = [col['name'] for col in inspector.get_columns('reminder_logs')]
    if 'days_before_expiry' not in columns:
        op.add_column('reminder_logs', sa.Column('days_before_expiry', sa.String(length=10), nullable=True))
        # 既存のレコードにはデフォルト値を設定
        connection.execute(text("UPDATE reminder_logs SET days_before_expiry = '7' WHERE days_before_expiry IS NULL"))
        connection.commit()
        # NOT NULL制約を追加
        op.alter_column('reminder_logs', 'days_before_expiry', nullable=False)


def downgrade() -> None:
    """
    reminder_logsテーブルからdays_before_expiryカラムを削除します。
    """
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    
    columns = [col['name'] for col in inspector.get_columns('reminder_logs')]
    if 'days_before_expiry' in columns:
        op.drop_column('reminder_logs', 'days_before_expiry')
