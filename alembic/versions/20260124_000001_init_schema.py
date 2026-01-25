"""init schema

Revision ID: 20260124_000001
Revises: 
Create Date: 2026-01-24 00:00:01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260124_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("ai_instruction_key", sa.String(), nullable=False),
        sa.Column("ai_instructions", sa.Text(), nullable=False),
        sa.Column("plot_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("plot_essentials", sa.Text(), nullable=False, server_default=""),
        sa.Column("author_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "lore_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("story_id", sa.String(), sa.ForeignKey("stories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("tag", sa.String(), nullable=False),
        sa.Column("triggers", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lore_entries_story_id", "lore_entries", ["story_id"])


def downgrade() -> None:
    op.drop_index("ix_lore_entries_story_id", table_name="lore_entries")
    op.drop_table("lore_entries")
    op.drop_table("stories")
