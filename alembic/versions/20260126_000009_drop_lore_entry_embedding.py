"""drop lore entry embedding

Revision ID: 20260126_000009
Revises: 20260126_000008
Create Date: 2026-01-26 00:00:09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260126_000009"
down_revision = "20260126_000008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("lore_entries") as batch_op:
        batch_op.drop_column("embedding")


def downgrade() -> None:
    from pgvector.sqlalchemy import Vector

    with op.batch_alter_table("lore_entries") as batch_op:
        batch_op.add_column(sa.Column("embedding", Vector(768), nullable=True))
