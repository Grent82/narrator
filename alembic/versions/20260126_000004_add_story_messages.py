"""add story messages

Revision ID: 20260126_000004
Revises: 20260125_000003
Create Date: 2026-01-26 00:00:04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260126_000004"
down_revision = "20260125_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stories",
        sa.Column("messages", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )


def downgrade() -> None:
    op.drop_column("stories", "messages")
