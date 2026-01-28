from __future__ import annotations

from datetime import UTC, datetime
from typing import List
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
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
    plot_essentials: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tags: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    messages: Mapped[List["StoryMessageModel"]] = relationship(
        "StoryMessageModel",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="StoryMessageModel.position",
    )
    summary_record: Mapped["StorySummaryModel | None"] = relationship(
        "StorySummaryModel",
        back_populates="story",
        cascade="all, delete-orphan",
        uselist=False,
    )
    lore_entries: Mapped[List["LoreEntryModel"]] = relationship(
        "LoreEntryModel",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="LoreEntryModel.created_at",
    )

    @property
    def plot_summary(self) -> str:
        if self.summary_record and self.summary_record.summary:
            return self.summary_record.summary
        return ""

    @plot_summary.setter
    def plot_summary(self, value: str) -> None:
        summary = (value or "").strip()
        if self.summary_record is None:
            self.summary_record = StorySummaryModel(summary=summary, last_position=-1)
        else:
            self.summary_record.summary = summary

class StoryMessageModel(Base):
    __tablename__ = "story_messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mode: Mapped[str | None] = mapped_column(String, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))

    story: Mapped["StoryModel"] = relationship("StoryModel", back_populates="messages")

    def to_payload(self) -> dict:
        data = {"role": self.role, "text": self.text or ""}
        if self.mode:
            data["mode"] = self.mode
        return data


class StorySummaryModel(Base):
    __tablename__ = "story_summaries"

    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), primary_key=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_position: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
    )

    story: Mapped["StoryModel"] = relationship("StoryModel", back_populates="summary_record")


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
