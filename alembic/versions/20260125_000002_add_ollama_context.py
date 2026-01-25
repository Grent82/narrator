"""add ollama context

Revision ID: 20260125_000002
Revises: 20260124_000001
Create Date: 2026-01-25 00:00:02
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260125_000002"
down_revision = "20260124_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stories",
        sa.Column(
            "ollama_context",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )


def downgrade() -> None:
    op.drop_column("stories", "ollama_context")
