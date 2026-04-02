"""change_users_role_from_varchar_to_enum

Revision ID: 30c935e130d0
Revises: 75c5d3bd8e0b
Create Date: 2026-03-31 20:15:56.838265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30c935e130d0'
down_revision: Union[str, Sequence[str], None] = '75c5d3bd8e0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE TYPE userrole AS ENUM ('customer', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR")
    op.execute("DROP TYPE userrole")
