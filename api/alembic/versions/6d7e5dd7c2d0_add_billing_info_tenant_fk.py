"""billing_infoテーブルにtenant_id外部キーを追加

Revision ID: 6d7e5dd7c2d0
Revises: 001238a78a22
Create Date: 2025-11-18 15:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = "6d7e5dd7c2d0"
down_revision = "001238a78a22"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    billing_info.tenant_id に tenants.id への外部キー制約を付与します。
    既に制約が存在する環境では何もしません。
    """
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_fk_names = {fk["name"] for fk in inspector.get_foreign_keys("billing_info")}

    constraint_name = "billing_info_tenant_id_fkey"
    if constraint_name not in existing_fk_names:
        op.create_foreign_key(
            constraint_name,
            source_table="billing_info",
            referent_table="tenants",
            local_cols=["tenant_id"],
            remote_cols=["id"],
        )


def downgrade() -> None:
    """
    追加した外部キー制約を削除します。
    """
    connection = op.get_bind()
    inspector = inspect(connection)
    existing_fk_names = {fk["name"] for fk in inspector.get_foreign_keys("billing_info")}

    constraint_name = "billing_info_tenant_id_fkey"
    if constraint_name in existing_fk_names:
        op.drop_constraint(constraint_name, "billing_info", type_="foreignkey")

