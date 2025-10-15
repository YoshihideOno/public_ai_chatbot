from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions required
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Common trigger function for updated_at
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # tenants
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('domain', sa.String(255), nullable=False, unique=True),
        sa.Column('plan', sa.String(50), nullable=False, server_default='FREE'),
        sa.Column('status', sa.String(50), nullable=False, server_default='ACTIVE'),
        sa.Column('api_key', sa.String(255), nullable=False, unique=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.CheckConstraint("plan IN ('FREE','BASIC','PRO','ENTERPRISE')", name='tenants_plan_check'),
        sa.CheckConstraint("status IN ('ACTIVE','SUSPENDED','DELETED')", name='tenants_status_check'),
    )
    op.create_index('idx_tenants_domain', 'tenants', ['domain'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_tenants_api_key', 'tenants', ['api_key'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_tenants_status', 'tenants', ['status'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.execute(
        """
        CREATE TRIGGER update_tenants_updated_at
        BEFORE UPDATE ON tenants
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )
    # RLS for tenants
    op.execute("ALTER TABLE tenants ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON tenants USING (id = current_setting('app.tenant_id')::uuid)")

    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='OPERATOR'),
        sa.Column('last_login_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.CheckConstraint("role IN ('PLATFORM_ADMIN','TENANT_ADMIN','OPERATOR','AUDITOR')", name='users_role_check'),
    )
    op.create_index('idx_users_tenant_id', 'users', ['tenant_id'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_users_email', 'users', ['email'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_users_role', 'users', ['role'], unique=False)
    op.execute(
        """
        CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY users_tenant_isolation ON users USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    # files
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='UPLOADED'),
        sa.Column('s3_key', sa.String(1000), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('indexed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.CheckConstraint("size_bytes > 0", name='files_size_bytes_check'),
        sa.CheckConstraint("chunk_count IS NULL OR chunk_count >= 0", name='files_chunk_count_check'),
        sa.CheckConstraint("file_type IN ('PDF','HTML','MD','CSV','TXT')", name='files_file_type_check'),
        sa.CheckConstraint("status IN ('UPLOADED','PROCESSING','INDEXED','FAILED')", name='files_status_check'),
    )
    op.create_index('idx_files_tenant_id', 'files', ['tenant_id', 'status'], unique=False, postgresql_where=sa.text('deleted_at IS NULL'))
    op.create_index('idx_files_status', 'files', ['status'], unique=False)
    op.create_index('idx_files_uploaded_at', 'files', ['uploaded_at'], unique=False, postgresql_using='btree')
    op.create_index('idx_files_s3_key', 'files', ['s3_key'], unique=False)
    op.execute(
        """
        CREATE TRIGGER update_files_updated_at
        BEFORE UPDATE ON files
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )
    op.execute("ALTER TABLE files ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY files_tenant_isolation ON files USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    # chunks with vector embedding and trigram indexes
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('vector_id', sa.String(255), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('file_id', 'chunk_index', name='chunks_file_chunk_unique'),
        sa.CheckConstraint('chunk_index >= 0', name='chunks_chunk_index_check'),
    )
    op.create_index('idx_chunks_file_id', 'chunks', ['file_id'], unique=False)
    op.create_index('idx_chunks_tenant_id', 'chunks', ['tenant_id'], unique=False)
    op.create_index('idx_chunks_vector_id', 'chunks', ['vector_id'], unique=False)
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN (metadata)")
    # pg_trgm trigram index for chunk_text
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunks_fulltext_trgm ON chunks USING GIN (chunk_text gin_trgm_ops)")
    # pgvector ivfflat index for embedding (optional use)
    op.execute("CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING ivfflat (embedding vector_l2_ops) WITH (lists=100)")

    # conversations
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_input', sa.Text(), nullable=False),
        sa.Column('bot_output', sa.Text(), nullable=False),
        sa.Column('referenced_chunks', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb")),
        sa.Column('tokens_in', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('tokens_out', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.String(50), nullable=True),
        sa.Column('feedback_comment', sa.Text(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('tokens_in >= 0', name='conversations_tokens_in_check'),
        sa.CheckConstraint('tokens_out >= 0', name='conversations_tokens_out_check'),
        sa.CheckConstraint("feedback IN ('LIKE','DISLIKE') OR feedback IS NULL", name='conversations_feedback_check'),
        sa.CheckConstraint('latency_ms IS NULL OR latency_ms > 0', name='conversations_latency_check'),
    )
    op.create_index('idx_conversations_tenant_id', 'conversations', ['tenant_id', 'created_at'], unique=False, postgresql_where=None)
    op.create_index('idx_conversations_session_id', 'conversations', ['session_id'], unique=False)
    op.create_index('idx_conversations_feedback', 'conversations', ['feedback'], unique=False, postgresql_where=sa.text('feedback IS NOT NULL'))
    op.create_index('idx_conversations_created_at', 'conversations', ['created_at'], unique=False)
    op.execute("CREATE INDEX IF NOT EXISTS idx_conversations_referenced_chunks ON conversations USING GIN (referenced_chunks)")
    op.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY conversations_tenant_isolation ON conversations USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    # usage_logs
    op.create_table(
        'usage_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('tokens_in', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('tokens_out', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('cost', sa.Numeric(10, 4), nullable=False, server_default=sa.text('0.0000')),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('tokens_in >= 0', name='usage_logs_tokens_in_check'),
        sa.CheckConstraint('tokens_out >= 0', name='usage_logs_tokens_out_check'),
        sa.CheckConstraint('cost >= 0', name='usage_logs_cost_check'),
        sa.CheckConstraint("provider IN ('OPENAI','ANTHROPIC','AZURE','COHERE')", name='usage_logs_provider_check'),
    )
    op.create_index('idx_usage_logs_tenant_id', 'usage_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('idx_usage_logs_model', 'usage_logs', ['model'], unique=False)
    op.create_index('idx_usage_logs_created_at', 'usage_logs', ['created_at'], unique=False)
    op.create_index('idx_usage_logs_conversation_id', 'usage_logs', ['conversation_id'], unique=False)
    op.execute("ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY usage_logs_tenant_isolation ON usage_logs USING (tenant_id = current_setting('app.tenant_id')::uuid)")

    # indexing_jobs
    op.create_table(
        'indexing_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('file_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='QUEUED'),
        sa.Column('started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('retry_count >= 0', name='indexing_jobs_retry_count_check'),
        sa.CheckConstraint("status IN ('QUEUED','RUNNING','SUCCESS','FAILED')", name='indexing_jobs_status_check'),
    )
    op.create_index('idx_indexing_jobs_file_id', 'indexing_jobs', ['file_id'], unique=False)
    op.create_index('idx_indexing_jobs_status', 'indexing_jobs', ['status'], unique=False)
    op.create_index('idx_indexing_jobs_created_at', 'indexing_jobs', ['created_at'], unique=False)
    op.execute(
        """
        CREATE TRIGGER update_indexing_jobs_updated_at
        BEFORE UPDATE ON indexing_jobs
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # billing_info
    op.create_table(
        'billing_info',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True, unique=True),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('billing_email', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('billing_address', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb")),
        sa.Column('tax_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("payment_method IN ('CARD','INVOICE') OR payment_method IS NULL", name='billing_info_payment_method_check'),
    )
    op.create_index('idx_billing_info_tenant_id', 'billing_info', ['tenant_id'], unique=False)
    op.create_index('idx_billing_info_stripe_customer_id', 'billing_info', ['stripe_customer_id'], unique=False)
    op.execute(
        """
        CREATE TRIGGER update_billing_info_updated_at
        BEFORE UPDATE ON billing_info
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # invoices
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('billing_info_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('billing_info.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_number', sa.String(100), nullable=False, unique=True),
        sa.Column('period_start', sa.Date(), nullable=False),
        sa.Column('period_end', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('tax', sa.Numeric(10, 2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('total', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='JPY'),
        sa.Column('status', sa.String(50), nullable=False, server_default='DRAFT'),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('pdf_url', sa.String(1000), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(255), nullable=True, unique=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("status IN ('DRAFT','SENT','PAID','OVERDUE','VOID')", name='invoices_status_check'),
        sa.CheckConstraint('period_end > period_start', name='invoices_period_check'),
        sa.CheckConstraint('amount >= 0', name='invoices_amount_check'),
        sa.CheckConstraint('tax >= 0', name='invoices_tax_check'),
        sa.CheckConstraint('total >= 0', name='invoices_total_check'),
    )
    op.create_index('idx_invoices_billing_info_id', 'invoices', ['billing_info_id'], unique=False)
    op.create_index('idx_invoices_invoice_number', 'invoices', ['invoice_number'], unique=False)
    op.create_index('idx_invoices_status', 'invoices', ['status'], unique=False)
    op.create_index('idx_invoices_period', 'invoices', ['period_start', 'period_end'], unique=False)
    op.create_index('idx_invoices_due_date', 'invoices', ['due_date'], unique=False)
    op.execute(
        """
        CREATE TRIGGER update_invoices_updated_at
        BEFORE UPDATE ON invoices
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
    )

    # audit_logs (WORM rules, partitions optional not created here)
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_audit_logs_tenant_id', 'audit_logs', ['tenant_id', 'created_at'], unique=False)
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('idx_audit_logs_resource', 'audit_logs', ['resource_type', 'resource_id'], unique=False)
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_details ON audit_logs USING GIN (details)")
    # WORM rules
    op.execute("CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING")
    op.execute("CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING")
    # RLS
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY audit_logs_tenant_isolation ON audit_logs USING (tenant_id = current_setting('app.tenant_id')::uuid)")


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP RULE IF EXISTS audit_logs_no_delete ON audit_logs")
    op.execute("DROP RULE IF EXISTS audit_logs_no_update ON audit_logs")
    op.drop_index('idx_audit_logs_details', table_name='audit_logs')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_resource', table_name='audit_logs')
    op.drop_index('idx_audit_logs_action', table_name='audit_logs')
    op.drop_index('idx_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('idx_audit_logs_tenant_id', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('idx_invoices_due_date', table_name='invoices')
    op.drop_index('idx_invoices_period', table_name='invoices')
    op.drop_index('idx_invoices_status', table_name='invoices')
    op.drop_index('idx_invoices_invoice_number', table_name='invoices')
    op.drop_index('idx_invoices_billing_info_id', table_name='invoices')
    op.drop_table('invoices')

    op.drop_index('idx_billing_info_stripe_customer_id', table_name='billing_info')
    op.drop_index('idx_billing_info_tenant_id', table_name='billing_info')
    op.drop_table('billing_info')

    op.drop_index('idx_indexing_jobs_created_at', table_name='indexing_jobs')
    op.drop_index('idx_indexing_jobs_status', table_name='indexing_jobs')
    op.drop_index('idx_indexing_jobs_file_id', table_name='indexing_jobs')
    op.drop_table('indexing_jobs')

    op.drop_index('idx_usage_logs_conversation_id', table_name='usage_logs')
    op.drop_index('idx_usage_logs_created_at', table_name='usage_logs')
    op.drop_index('idx_usage_logs_model', table_name='usage_logs')
    op.drop_index('idx_usage_logs_tenant_id', table_name='usage_logs')
    op.drop_table('usage_logs')

    op.drop_index('idx_conversations_referenced_chunks', table_name='conversations')
    op.drop_index('idx_conversations_created_at', table_name='conversations')
    op.drop_index('idx_conversations_feedback', table_name='conversations')
    op.drop_index('idx_conversations_session_id', table_name='conversations')
    op.drop_index('idx_conversations_tenant_id', table_name='conversations')
    op.drop_table('conversations')

    op.execute('DROP INDEX IF EXISTS idx_chunks_embedding')
    op.execute('DROP INDEX IF EXISTS idx_chunks_fulltext_trgm')
    op.execute('DROP INDEX IF EXISTS idx_chunks_metadata')
    op.drop_index('idx_chunks_vector_id', table_name='chunks')
    op.drop_index('idx_chunks_tenant_id', table_name='chunks')
    op.drop_index('idx_chunks_file_id', table_name='chunks')
    op.drop_table('chunks')

    op.drop_index('idx_files_s3_key', table_name='files')
    op.drop_index('idx_files_uploaded_at', table_name='files')
    op.drop_index('idx_files_status', table_name='files')
    op.drop_index('idx_files_tenant_id', table_name='files')
    op.drop_table('files')

    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_index('idx_users_tenant_id', table_name='users')
    op.drop_table('users')

    op.drop_index('idx_tenants_status', table_name='tenants')
    op.drop_index('idx_tenants_api_key', table_name='tenants')
    op.drop_index('idx_tenants_domain', table_name='tenants')
    op.drop_table('tenants')

    # Keep extensions installed
