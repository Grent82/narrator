"""add lore suggestions

Revision ID: 20260129_000012
Revises: 20260128_000011
Create Date: 2026-01-29 00:00:12
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260129_000012"
down_revision = "20260128_000011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lore_suggestions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("tag", sa.String(), nullable=False, server_default="Character"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("triggers", sa.Text(), nullable=False, server_default=""),
        sa.Column("target_lore_id", sa.String(), nullable=True),
        sa.Column("source_user", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_assistant", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lore_suggestions_story_id", "lore_suggestions", ["story_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_lore_suggestions_story_id", table_name="lore_suggestions")
    op.drop_table("lore_suggestions")
