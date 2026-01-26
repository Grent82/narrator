"""move story messages and context to separate tables

Revision ID: 20260126_000005
Revises: 20260126_000004
Create Date: 2026-01-26 00:00:05
"""
from __future__ import annotations

import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260126_000005"
down_revision = "20260126_000004"
branch_labels = None
depends_on = None


def _coerce_json(value):
    if value is None:
        return []
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value


def upgrade() -> None:
    op.create_table(
        "story_ollama_contexts",
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("story_id"),
    )
    op.create_table(
        "story_messages",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_story_messages_story_id", "story_messages", ["story_id"], unique=False)

    conn = op.get_bind()
    stories = conn.execute(sa.text("SELECT id, messages, ollama_context FROM stories")).mappings().all()

    message_table = sa.table(
        "story_messages",
        sa.column("id", sa.String()),
        sa.column("story_id", sa.String()),
        sa.column("role", sa.String()),
        sa.column("text", sa.Text()),
        sa.column("mode", sa.String()),
        sa.column("position", sa.Integer()),
    )
    context_table = sa.table(
        "story_ollama_contexts",
        sa.column("story_id", sa.String()),
        sa.column("context", sa.JSON()),
    )

    for row in stories:
        story_id = row["id"]
        context = _coerce_json(row.get("ollama_context"))
        if not isinstance(context, list):
            context = []
        conn.execute(context_table.insert().values(story_id=story_id, context=context))

        messages = _coerce_json(row.get("messages"))
        if isinstance(messages, list):
            for position, msg in enumerate(messages):
                payload = msg if isinstance(msg, dict) else {}
                conn.execute(
                    message_table.insert().values(
                        id=str(payload.get("id") or uuid4()),
                        story_id=story_id,
                        role=str(payload.get("role", "")).strip(),
                        text=str(payload.get("text", "") or ""),
                        mode=payload.get("mode"),
                        position=position,
                    )
                )

    with op.batch_alter_table("stories") as batch_op:
        batch_op.drop_column("messages")
        batch_op.drop_column("ollama_context")


def downgrade() -> None:
    with op.batch_alter_table("stories") as batch_op:
        batch_op.add_column(
            sa.Column("ollama_context", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )
        batch_op.add_column(
            sa.Column("messages", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        )

    conn = op.get_bind()
    stories = conn.execute(sa.text("SELECT id FROM stories")).mappings().all()
    story_rows = {row["id"]: {"messages": [], "context": []} for row in stories}

    contexts = conn.execute(sa.text("SELECT story_id, context FROM story_ollama_contexts")).mappings().all()
    for row in contexts:
        story_rows.setdefault(row["story_id"], {})["context"] = _coerce_json(row.get("context"))

    messages = conn.execute(
        sa.text("SELECT story_id, role, text, mode, position FROM story_messages ORDER BY position ASC")
    ).mappings().all()
    for row in messages:
        entry = {
            "role": row.get("role", ""),
            "text": row.get("text", "") or "",
        }
        if row.get("mode"):
            entry["mode"] = row.get("mode")
        story_rows.setdefault(row["story_id"], {}).setdefault("messages", []).append(entry)

    for story_id, payload in story_rows.items():
        conn.execute(
            sa.text(
                "UPDATE stories SET messages = :messages, ollama_context = :context WHERE id = :story_id"
            ),
            {
                "messages": json.dumps(payload.get("messages", [])),
                "context": json.dumps(payload.get("context", [])),
                "story_id": story_id,
            },
        )

    op.drop_index("ix_story_messages_story_id", table_name="story_messages")
    op.drop_table("story_messages")
    op.drop_table("story_ollama_contexts")
