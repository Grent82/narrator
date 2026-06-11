"""add_locations_table_and_location_tracking

Revision ID: 09dfab85be31
Revises: 20260129_000012
Create Date: 2026-06-11 15:44:32.056394
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '09dfab85be31'
down_revision = '20260129_000012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, default=""),
        sa.Column("tag", sa.String(length=100), nullable=False, default="Location"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
    )

    # Create unique constraint on story_id + name
    op.create_unique_constraint("uq_locations_story_name", "locations", ["story_id", "name"])

    # Create index on story_id
    op.create_index("idx_locations_story_id", "locations", ["story_id"])

    # Add location_id column to story_messages
    op.add_column("story_messages", sa.Column("location_id", sa.String(), nullable=True))

    # Create index on location_id
    op.create_index("idx_story_messages_location_id", "story_messages", ["location_id"])

    # Add foreign key constraint (SET NULL on delete)
    op.create_foreign_key(
        "fk_story_messages_location_id",
        "story_messages",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint("fk_story_messages_location_id", "story_messages", type_="foreignkey")

    # Drop index on location_id
    op.drop_index("idx_story_messages_location_id", "story_messages")

    # Drop location_id column
    op.drop_column("story_messages", "location_id")

    # Drop index on story_id
    op.drop_index("idx_locations_story_id", "locations")

    # Drop unique constraint
    op.drop_constraint("uq_locations_story_name", "locations", type_="unique")

    # Drop locations table
    op.drop_table("locations")
