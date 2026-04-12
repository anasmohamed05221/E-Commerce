"""add_stock_non_negative_check_constraint

Revision ID: f628a7d18bde
Revises: fe2ede2c0ed0
Create Date: 2026-04-12 22:14:47.129598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f628a7d18bde'
down_revision: Union[str, Sequence[str], None] = 'fe2ede2c0ed0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint("ck_product_stock_non_negative", "products", "stock >= 0")

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_product_stock_non_negative", "products", type_="check")
