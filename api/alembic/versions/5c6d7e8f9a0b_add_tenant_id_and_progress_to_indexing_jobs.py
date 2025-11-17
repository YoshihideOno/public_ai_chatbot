"""add tenant_id and progress to indexing_jobs

Revision ID: 5c6d7e8f9a0b
Revises: 4b9f2a1c0b2a
Create Date: 2025-01-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5c6d7e8f9a0b'
down_revision = '4b9f2a1c0b2a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    indexing_jobsテーブルは廃止されたため、このマイグレーションは何もしません。
    """
    pass


def downgrade() -> None:
    """
    indexing_jobsテーブルは廃止されたため、このマイグレーションは何もしません。
    """
    pass

