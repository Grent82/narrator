"""remove story ollama contexts

Revision ID: 20260126_000007
Revises: 20260126_000006
Create Date: 2026-01-26 00:00:07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260126_000007"
down_revision = "20260126_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("story_ollama_contexts")


def downgrade() -> None:
    op.create_table(
        "story_ollama_contexts",
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("story_id"),
    )
