"""add_shipped_to_order_status_enum

Revision ID: 1dc4f42a39b8
Revises: 9272d7a77a35
Create Date: 2026-04-12 21:41:32.598863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1dc4f42a39b8'
down_revision: Union[str, Sequence[str], None] = '9272d7a77a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("COMMIT")
    op.execute("ALTER TYPE order_status ADD VALUE IF NOT EXISTS 'shipped'")

def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support removing enum values.
    # To fully revert, the type would need to be dropped and recreated,
    # which requires dropping all columns that use it.
    pass