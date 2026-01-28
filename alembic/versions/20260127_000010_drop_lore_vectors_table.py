"""drop lore_vectors table

Revision ID: 20260127_000010
Revises: 20260126_000009
Create Date: 2026-01-27 00:00:10
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260127_000010"
down_revision = "20260126_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS lore_vectors")


def downgrade() -> None:
    pass
