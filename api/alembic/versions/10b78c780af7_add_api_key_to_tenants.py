"""add_api_key_to_tenants

Revision ID: 10b78c780af7
Revises: c143e943d08c
Create Date: 2025-11-08 15:26:41.988971

"""
from alembic import op
import sqlalchemy as sa
import secrets
import string


# revision identifiers, used by Alembic.
revision = '10b78c780af7'
down_revision = 'c143e943d08c'
branch_labels = None
depends_on = None


def generate_api_key() -> str:
    """ランダムなAPIキーを生成"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def upgrade() -> None:
    """
    api_keyカラムを追加します。
    初期マイグレーションで既に作成されている場合は、既存のテナントにAPIキーを生成するのみです。
    """
    from sqlalchemy import inspect, text
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # api_keyカラムが存在するかチェック
    columns = [col['name'] for col in inspector.get_columns('tenants')]
    api_key_exists = 'api_key' in columns
    
    if not api_key_exists:
        # api_keyカラムを追加（既存のテナントには一時的にNULLを許可）
        op.add_column('tenants', sa.Column('api_key', sa.String(length=255), nullable=True))
    
    # 既存のテナントに対してランダムなAPIキーを生成（api_keyがNULLの場合のみ）
    result = connection.execute(text("SELECT id FROM tenants WHERE api_key IS NULL"))
    tenants = result.fetchall()
    
    for tenant in tenants:
        tenant_id = tenant[0]
        api_key = generate_api_key()
        # ユニーク制約を満たすまで再生成
        while True:
            check_result = connection.execute(
                text("SELECT COUNT(*) FROM tenants WHERE api_key = :api_key"),
                {"api_key": api_key}
            )
            if check_result.scalar() == 0:
                break
            api_key = generate_api_key()
        
        # UUIDを文字列に変換してUPDATE
        connection.execute(
            text("UPDATE tenants SET api_key = :api_key WHERE id = :tenant_id"),
            {"api_key": api_key, "tenant_id": str(tenant_id)}
        )
        connection.commit()
    
    # NULLを許可しないように変更（既にNOT NULLの場合はスキップ）
    if not api_key_exists:
        op.alter_column('tenants', 'api_key', nullable=False)
    
    # ユニーク制約を追加（既に存在する場合はスキップ）
    constraints = inspector.get_unique_constraints('tenants')
    constraint_names = [c['name'] for c in constraints]
    # api_keyを含むユニーク制約が既に存在するかチェック
    has_api_key_unique = any('api_key' in c['column_names'] for c in constraints)
    
    if not has_api_key_unique and 'uq_tenants_api_key' not in constraint_names:
        op.create_unique_constraint('uq_tenants_api_key', 'tenants', ['api_key'])


def downgrade() -> None:
    """
    api_keyカラムとユニーク制約を削除します。
    初期マイグレーションで作成された場合は、カラムは削除しません。
    """
    from sqlalchemy import inspect
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # ユニーク制約を削除（存在する場合のみ）
    constraints = [c['name'] for c in inspector.get_unique_constraints('tenants')]
    if 'uq_tenants_api_key' in constraints:
        op.drop_constraint('uq_tenants_api_key', 'tenants', type_='unique')
    
    # api_keyカラムがこのマイグレーションで追加された場合のみ削除
    # 初期マイグレーションで作成された場合は削除しない
    # （初期マイグレーションのdown_revisionを確認する必要があるが、
    #  安全のため、このマイグレーションではカラムを削除しない）
    # 注意: 初期マイグレーションで作成されたapi_keyカラムは、このマイグレーションでは削除されません
