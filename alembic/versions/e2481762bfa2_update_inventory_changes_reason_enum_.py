"""update inventory_changes reason enum values

Revision ID: e2481762bfa2
Revises: 0990fa59ceb8
Create Date: 2026-03-26 21:32:51.321673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2481762bfa2'
down_revision: Union[str, Sequence[str], None] = '0990fa59ceb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column("inventory_changes", "reason")
    op.execute("DROP TYPE reason")
    op.execute("CREATE TYPE reason AS ENUM ('sale', 'restock', 'adjustment', 'return', 'cancellation')")
    op.add_column("inventory_changes", sa.Column("reason", sa.Enum("sale", "restock", "adjustment", "return", "cancellation", name="reason")))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inventory_changes", "reason")
    op.execute("DROP TYPE reason")
    op.execute("CREATE TYPE reason AS ENUM ('increment', 'decrement')")
    op.add_column("inventory_changes", sa.Column("reason", sa.Enum("increment", "decrement", name="reason")))
