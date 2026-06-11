"""add_worldview_settings_table

Revision ID: 532b1c8db9b3
Revises: 09dfab85be31
Create Date: 2026-06-11 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '532b1c8db9b3'
down_revision = '09dfab85be31'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create worldview_settings table
    op.create_table(
        "worldview_settings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("term", sa.String(length=255), nullable=False),
        sa.Column("nature", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
    )

    # Create unique constraint on story_id + term + nature
    op.create_unique_constraint("uq_worldview_story_term_nature", "worldview_settings", ["story_id", "term", "nature"])

    # Create indexes
    op.create_index("idx_worldview_settings_story_id", "worldview_settings", ["story_id"])
    op.create_index("idx_worldview_settings_term", "worldview_settings", ["term"])
    op.create_index("idx_worldview_settings_nature", "worldview_settings", ["nature"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("idx_worldview_settings_nature", "worldview_settings")
    op.drop_index("idx_worldview_settings_term", "worldview_settings")
    op.drop_index("idx_worldview_settings_story_id", "worldview_settings")

    # Drop unique constraint
    op.drop_constraint("uq_worldview_story_term_nature", "worldview_settings", type_="unique")

    # Drop table
    op.drop_table("worldview_settings")
