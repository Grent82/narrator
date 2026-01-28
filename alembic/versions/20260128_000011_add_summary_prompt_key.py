"""add summary prompt key

Revision ID: 20260128_000011
Revises: 20260127_000010
Create Date: 2026-01-28 00:00:11
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260128_000011"
down_revision = "20260127_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stories",
        sa.Column("summary_prompt_key", sa.String(), nullable=False, server_default="neutral"),
    )


def downgrade() -> None:
    op.drop_column("stories", "summary_prompt_key")
