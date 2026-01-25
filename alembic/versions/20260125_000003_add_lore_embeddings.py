"""add lore embeddings

Revision ID: 20260125_000003
Revises: 20260125_000002
Create Date: 2026-01-25 00:00:03
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20260125_000003"
down_revision = "20260125_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "lore_entries",
        sa.Column("embedding", Vector(768), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("lore_entries", "embedding")
