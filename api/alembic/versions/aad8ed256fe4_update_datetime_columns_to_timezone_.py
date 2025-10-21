"""update_datetime_columns_to_timezone_aware

Revision ID: aad8ed256fe4
Revises: ae01f2ea5e65
Create Date: 2025-10-20 11:47:40.802718

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aad8ed256fe4'
down_revision = 'ae01f2ea5e65'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    すべてのDateTimeカラムをtimezone awareに変更
    """
    # audit_logs テーブル
    op.alter_column('audit_logs', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # conversations テーブル
    op.alter_column('conversations', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # usage_logs テーブル
    op.alter_column('usage_logs', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # tenants テーブル
    op.alter_column('tenants', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('tenants', 'updated_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('tenants', 'deleted_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    
    # files テーブル
    op.alter_column('files', 'uploaded_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('files', 'indexed_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('files', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('files', 'updated_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('files', 'deleted_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    
    # chunks テーブル
    op.alter_column('chunks', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # indexing_jobs テーブル
    op.alter_column('indexing_jobs', 'started_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('indexing_jobs', 'completed_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('indexing_jobs', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('indexing_jobs', 'updated_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # billing_info テーブル
    op.alter_column('billing_info', 'current_period_start',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('billing_info', 'current_period_end',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('billing_info', 'trial_end',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('billing_info', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('billing_info', 'updated_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    
    # invoices テーブル
    op.alter_column('invoices', 'paid_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=True)
    op.alter_column('invoices', 'created_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)
    op.alter_column('invoices', 'updated_at',
                   existing_type=sa.DateTime(timezone=False),
                   type_=sa.DateTime(timezone=True),
                   existing_nullable=False)


def downgrade() -> None:
    """
    すべてのDateTimeカラムをtimezone unawareに戻す
    """
    # audit_logs テーブル
    op.alter_column('audit_logs', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # conversations テーブル
    op.alter_column('conversations', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # usage_logs テーブル
    op.alter_column('usage_logs', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # tenants テーブル
    op.alter_column('tenants', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('tenants', 'updated_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('tenants', 'deleted_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    
    # files テーブル
    op.alter_column('files', 'uploaded_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('files', 'indexed_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('files', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('files', 'updated_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('files', 'deleted_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    
    # chunks テーブル
    op.alter_column('chunks', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # indexing_jobs テーブル
    op.alter_column('indexing_jobs', 'started_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('indexing_jobs', 'completed_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('indexing_jobs', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('indexing_jobs', 'updated_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # billing_info テーブル
    op.alter_column('billing_info', 'current_period_start',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('billing_info', 'current_period_end',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('billing_info', 'trial_end',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('billing_info', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('billing_info', 'updated_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    
    # invoices テーブル
    op.alter_column('invoices', 'paid_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=True)
    op.alter_column('invoices', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
    op.alter_column('invoices', 'updated_at',
                   existing_type=sa.DateTime(timezone=True),
                   type_=sa.DateTime(timezone=False),
                   existing_nullable=False)
