"""drop chats and tokens columns

Revision ID: 79c3d1e5b6ef
Revises: 5c6d7e8f9a0b, 10b78c780af7
Create Date: 2025-11-11 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '79c3d1e5b6ef'
down_revision = ('5c6d7e8f9a0b', '10b78c780af7')
branch_labels = None
depends_on = None


CHATS_TABLE = 'chats'
MESSAGES_TABLE = 'messages'
CONVERSATIONS_TABLE = 'conversations'
TOKENS_IN_COLUMN = 'tokens_in'
TOKENS_OUT_COLUMN = 'tokens_out'


def upgrade() -> None:
    """chats/messagesテーブルとconversationsトークン列を削除"""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if MESSAGES_TABLE in existing_tables:
        op.drop_table(MESSAGES_TABLE)

    if CHATS_TABLE in existing_tables:
        op.drop_table(CHATS_TABLE)

    if CONVERSATIONS_TABLE in existing_tables:
        conversation_columns = {col['name'] for col in inspector.get_columns(CONVERSATIONS_TABLE)}
        if TOKENS_IN_COLUMN in conversation_columns:
            op.drop_column(CONVERSATIONS_TABLE, TOKENS_IN_COLUMN)
        if TOKENS_OUT_COLUMN in conversation_columns:
            op.drop_column(CONVERSATIONS_TABLE, TOKENS_OUT_COLUMN)


def downgrade() -> None:
    """chats/messagesテーブルとconversationsトークン列を復元"""
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if CHATS_TABLE not in existing_tables:
        op.create_table(
            CHATS_TABLE,
            sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_chats_id'), CHATS_TABLE, ['id'], unique=False)

    if MESSAGES_TABLE not in existing_tables:
        op.create_table(
            MESSAGES_TABLE,
            sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
            sa.Column('chat_id', sa.UUID(), nullable=False),
            sa.Column('role', sa.String(length=20), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_messages_id'), MESSAGES_TABLE, ['id'], unique=False)

    if CONVERSATIONS_TABLE in existing_tables:
        conversation_columns = {col['name'] for col in inspector.get_columns(CONVERSATIONS_TABLE)}
        if TOKENS_IN_COLUMN not in conversation_columns:
            op.add_column(CONVERSATIONS_TABLE, sa.Column(TOKENS_IN_COLUMN, sa.Integer(), nullable=False, server_default='0'))
            op.execute(sa.text(f"ALTER TABLE {CONVERSATIONS_TABLE} ALTER COLUMN {TOKENS_IN_COLUMN} DROP DEFAULT"))
        if TOKENS_OUT_COLUMN not in conversation_columns:
            op.add_column(CONVERSATIONS_TABLE, sa.Column(TOKENS_OUT_COLUMN, sa.Integer(), nullable=False, server_default='0'))
            op.execute(sa.text(f"ALTER TABLE {CONVERSATIONS_TABLE} ALTER COLUMN {TOKENS_OUT_COLUMN} DROP DEFAULT"))

    # 外部キー制約を追加（存在しない場合のみ）
    if CHATS_TABLE in inspector.get_table_names() and MESSAGES_TABLE in inspector.get_table_names():
        fk_names = {fk['name'] for fk in inspector.get_foreign_keys(MESSAGES_TABLE)}
        if 'messages_chat_id_fkey' not in fk_names:
            op.create_foreign_key(None, MESSAGES_TABLE, CHATS_TABLE, ['chat_id'], ['id'])

    if CHATS_TABLE in inspector.get_table_names():
        fk_names = {fk['name'] for fk in inspector.get_foreign_keys(CHATS_TABLE)}
        if 'chats_user_id_fkey' not in fk_names:
            op.create_foreign_key(None, CHATS_TABLE, 'users', ['user_id'], ['id'])
