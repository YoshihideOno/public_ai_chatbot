"""create_missing_tables_usage_logs_conversations_audit_logs_reminder_logs_notifications_billing_invoices_verification_tokens

Revision ID: 001238a78a22
Revises: 4ce9e08004a9
Create Date: 2025-11-18 17:16:28.076782

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '001238a78a22'
down_revision = '4ce9e08004a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    モデル定義に存在するがマイグレーションファイルで作成されていないテーブルを作成します。
    """
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    
    # usage_logs テーブル
    if 'usage_logs' not in existing_tables:
        op.create_table(
            'usage_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('tokens_in', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('tokens_out', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('cost', sa.Numeric(10, 4), nullable=False, server_default='0'),
            sa.Column('provider', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        )
        op.create_index(op.f('ix_usage_logs_tenant_id'), 'usage_logs', ['tenant_id'], unique=False)
    
    # conversations テーブル
    if 'conversations' not in existing_tables:
        op.create_table(
            'conversations',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_id', sa.String(length=255), nullable=False),
            sa.Column('user_input', sa.Text(), nullable=False),
            sa.Column('bot_output', sa.Text(), nullable=False),
            sa.Column('referenced_chunks', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
            sa.Column('model', sa.String(length=100), nullable=False),
            sa.Column('latency_ms', sa.Integer(), nullable=True),
            sa.Column('feedback', sa.String(length=50), nullable=True),
            sa.Column('feedback_comment', sa.Text(), nullable=True),
            sa.Column('ip_address', postgresql.INET(), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        )
        op.create_index(op.f('ix_conversations_tenant_id'), 'conversations', ['tenant_id'], unique=False)
    
    # audit_logs テーブル
    if 'audit_logs' not in existing_tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('resource_type', sa.String(length=100), nullable=False),
            sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('ip_address', postgresql.INET(), nullable=False),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        )
        op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    # reminder_logs テーブル
    if 'reminder_logs' not in existing_tables:
        op.create_table(
            'reminder_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('reminder_type', sa.String(length=20), nullable=False),
            sa.Column('days_before_expiry', sa.String(length=10), nullable=True),
            sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_sent', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('send_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('failure_reason', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        )
        op.create_index(op.f('ix_reminder_logs_tenant_id'), 'reminder_logs', ['tenant_id'], unique=False)
    
    # notifications テーブル
    if 'notifications' not in existing_tables:
        op.create_table(
            'notifications',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('notification_type', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=True),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        )
        op.create_index(op.f('ix_notifications_tenant_id'), 'notifications', ['tenant_id'], unique=False)
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    
    # billing_info テーブル
    if 'billing_info' not in existing_tables:
        op.create_table(
            'billing_info',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
            sa.Column('stripe_payment_method_id', sa.String(length=255), nullable=True),
            sa.Column('plan', sa.String(length=50), nullable=False, server_default='FREE'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
            sa.Column('billing_cycle', sa.String(length=50), nullable=False, server_default='MONTHLY'),
            sa.Column('billing_email', sa.String(length=255), nullable=False),
            sa.Column('company_name', sa.String(length=255), nullable=True),
            sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
            sa.Column('tax_id', sa.String(length=100), nullable=True),
            sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
            sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('quota_queries', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('quota_storage_mb', sa.Integer(), nullable=False, server_default='100'),
            sa.Column('usage_queries', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('usage_storage_mb', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('tenant_id'),
            sa.UniqueConstraint('stripe_customer_id'),
            sa.UniqueConstraint('stripe_subscription_id'),
        )
        op.create_index(op.f('ix_billing_info_tenant_id'), 'billing_info', ['tenant_id'], unique=True)
    
    # invoices テーブル
    if 'invoices' not in existing_tables:
        op.create_table(
            'invoices',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('billing_info_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('stripe_invoice_id', sa.String(length=255), nullable=True),
            sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
            sa.Column('invoice_number', sa.String(length=100), nullable=False),
            sa.Column('period_start', sa.Date(), nullable=False),
            sa.Column('period_end', sa.Date(), nullable=False),
            sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
            sa.Column('tax', sa.Numeric(10, 2), nullable=False, server_default='0'),
            sa.Column('total', sa.Numeric(10, 2), nullable=False),
            sa.Column('currency', sa.String(length=3), nullable=False, server_default='JPY'),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
            sa.Column('due_date', sa.Date(), nullable=False),
            sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('pdf_url', sa.String(length=1000), nullable=True),
            sa.Column('line_items', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('stripe_invoice_id'),
            sa.UniqueConstraint('invoice_number'),
            sa.ForeignKeyConstraint(['billing_info_id'], ['billing_info.id'], ),
        )
        op.create_index(op.f('ix_invoices_billing_info_id'), 'invoices', ['billing_info_id'], unique=False)
    
    # verification_tokens テーブル
    if 'verification_tokens' not in existing_tables:
        op.create_table(
            'verification_tokens',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('token_type', sa.String(length=50), nullable=False, server_default='email_verification'),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_used', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        )
        op.create_index(op.f('ix_verification_tokens_user_id'), 'verification_tokens', ['user_id'], unique=False)
        op.create_index(op.f('ix_verification_tokens_id'), 'verification_tokens', ['id'], unique=False)
        op.create_index(op.f('ix_verification_tokens_token'), 'verification_tokens', ['token'], unique=False)


def downgrade() -> None:
    """
    作成したテーブルを削除します。
    """
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    
    # 外部キー制約があるため、依存関係の逆順で削除
    if 'verification_tokens' in existing_tables:
        op.drop_index(op.f('ix_verification_tokens_token'), table_name='verification_tokens')
        op.drop_index(op.f('ix_verification_tokens_id'), table_name='verification_tokens')
        op.drop_index(op.f('ix_verification_tokens_user_id'), table_name='verification_tokens')
        op.drop_table('verification_tokens')
    
    if 'invoices' in existing_tables:
        op.drop_index(op.f('ix_invoices_billing_info_id'), table_name='invoices')
        op.drop_table('invoices')
    
    if 'billing_info' in existing_tables:
        op.drop_index(op.f('ix_billing_info_tenant_id'), table_name='billing_info')
        op.drop_table('billing_info')
    
    if 'notifications' in existing_tables:
        op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
        op.drop_index(op.f('ix_notifications_tenant_id'), table_name='notifications')
        op.drop_table('notifications')
    
    if 'reminder_logs' in existing_tables:
        op.drop_index(op.f('ix_reminder_logs_tenant_id'), table_name='reminder_logs')
        op.drop_table('reminder_logs')
    
    if 'audit_logs' in existing_tables:
        op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
        op.drop_index(op.f('ix_audit_logs_tenant_id'), table_name='audit_logs')
        op.drop_table('audit_logs')
    
    if 'conversations' in existing_tables:
        op.drop_index(op.f('ix_conversations_tenant_id'), table_name='conversations')
        op.drop_table('conversations')
    
    if 'usage_logs' in existing_tables:
        op.drop_index(op.f('ix_usage_logs_tenant_id'), table_name='usage_logs')
        op.drop_table('usage_logs')
