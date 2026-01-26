"""add lore vectors

Revision ID: 20260126_000008
Revises: 20260126_000007
Create Date: 2026-01-26 00:00:08
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = "20260126_000008"
down_revision = "20260126_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lore_vectors",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("lore_id", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lore_vectors_story_id", "lore_vectors", ["story_id"], unique=False)
    op.create_index("ix_lore_vectors_story_lore", "lore_vectors", ["story_id", "lore_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_lore_vectors_story_lore", table_name="lore_vectors")
    op.drop_index("ix_lore_vectors_story_id", table_name="lore_vectors")
    op.drop_table("lore_vectors")
