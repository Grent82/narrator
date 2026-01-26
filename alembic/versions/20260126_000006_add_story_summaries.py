"""add story summaries table

Revision ID: 20260126_000006
Revises: 20260126_000005
Create Date: 2026-01-26 00:00:06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260126_000006"
down_revision = "20260126_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "story_summaries",
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("last_position", sa.Integer(), nullable=False, server_default=sa.text("-1")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("story_id"),
    )

    conn = op.get_bind()
    summaries = conn.execute(sa.text("SELECT id, plot_summary FROM stories")).mappings().all()
    positions = conn.execute(
        sa.text("SELECT story_id, MAX(position) AS last_position FROM story_messages GROUP BY story_id")
    ).mappings().all()
    position_map = {row["story_id"]: row["last_position"] for row in positions}

    summary_table = sa.table(
        "story_summaries",
        sa.column("story_id", sa.String()),
        sa.column("summary", sa.Text()),
        sa.column("last_position", sa.Integer()),
    )
    for row in summaries:
        story_id = row["id"]
        summary = row.get("plot_summary") or ""
        last_position = position_map.get(story_id, -1)
        conn.execute(
            summary_table.insert().values(
                story_id=story_id,
                summary=summary,
                last_position=last_position if last_position is not None else -1,
            )
        )

    with op.batch_alter_table("stories") as batch_op:
        batch_op.drop_column("plot_summary")


def downgrade() -> None:
    with op.batch_alter_table("stories") as batch_op:
        batch_op.add_column(
            sa.Column("plot_summary", sa.Text(), nullable=False, server_default=sa.text("''")),
        )

    conn = op.get_bind()
    summaries = conn.execute(sa.text("SELECT story_id, summary FROM story_summaries")).mappings().all()
    for row in summaries:
        conn.execute(
            sa.text("UPDATE stories SET plot_summary = :summary WHERE id = :story_id"),
            {"summary": row.get("summary", "") or "", "story_id": row["story_id"]},
        )

    op.drop_table("story_summaries")
