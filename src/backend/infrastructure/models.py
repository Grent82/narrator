from datetime import UTC, datetime
from typing import List
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from src.backend.infrastructure.db import Base


def _generate_id() -> str:
    return str(uuid4())



class StoryModel(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    title: Mapped[str] = mapped_column(String, nullable=False)
    ai_instruction_key: Mapped[str] = mapped_column(String, nullable=False)
    ai_instructions: Mapped[str] = mapped_column(Text, nullable=False)
    plot_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    plot_essentials: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    lore_entries: Mapped[List["LoreEntryModel"]] = relationship(
        "LoreEntryModel",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="LoreEntryModel.created_at",
    )


class LoreEntryModel(Base):
    __tablename__ = "lore_entries"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tag: Mapped[str] = mapped_column(String, nullable=False)
    triggers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    story: Mapped[StoryModel] = relationship("StoryModel", back_populates="lore_entries")
