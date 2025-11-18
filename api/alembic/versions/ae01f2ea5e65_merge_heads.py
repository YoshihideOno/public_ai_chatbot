"""merge_heads

Revision ID: ae01f2ea5e65
Revises: 03b760e5716a, f3d0f1670e29
Create Date: 2025-10-18 14:23:23.214086

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae01f2ea5e65'
down_revision = ('03b760e5716a', 'f3d0f1670e29')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
