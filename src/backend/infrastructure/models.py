from __future__ import annotations

from datetime import datetime
from typing import List

try:
    from datetime import UTC
except ImportError:
    # Python 3.10 compatibility
    from datetime import timezone

    UTC = timezone.utc
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
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
    summary_prompt_key: Mapped[str] = mapped_column(String, nullable=False, default="neutral_summarizer")
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
    lore_suggestions: Mapped[List["LoreSuggestionModel"]] = relationship(
        "LoreSuggestionModel",
        back_populates="story",
        cascade="all, delete-orphan",
        order_by="LoreSuggestionModel.created_at",
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


class LoreSuggestionModel(Base):
    __tablename__ = "lore_suggestions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # NEW | UPDATE
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")  # pending|accepted|rejected
    title: Mapped[str] = mapped_column(String, nullable=False)
    tag: Mapped[str] = mapped_column(String, nullable=False, default="Character")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    triggers: Mapped[str] = mapped_column(Text, nullable=False, default="")
    target_lore_id: Mapped[str | None] = mapped_column(String, nullable=True)
    source_user: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_assistant: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))

    story: Mapped[StoryModel] = relationship("StoryModel", back_populates="lore_suggestions")


class LocationModel(Base):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    tag: Mapped[str] = mapped_column(String(length=100), nullable=False, server_default="Location")
    location_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    story: Mapped["StoryModel"] = relationship("StoryModel", back_populates="locations")


class TravelTaskModel(Base):
    __tablename__ = "travel_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    character_name: Mapped[str] = mapped_column(String(255), nullable=False)
    from_location_id: Mapped[str | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    to_location_id: Mapped[str] = mapped_column(ForeignKey("locations.id", ondelete="CASCADE"), nullable=False)
    distance: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    remaining_turns: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="in_progress")

    story: Mapped["StoryModel"] = relationship("StoryModel", back_populates="travel_tasks")


# Add relationships to StoryModel
StoryModel.locations = relationship("LocationModel", back_populates="story", cascade="all, delete-orphan", order_by="LocationModel.name")
StoryModel.travel_tasks = relationship("TravelTaskModel", back_populates="story", cascade="all, delete-orphan", order_by="TravelTaskModel.started_at")

# Add location_id to StoryMessageModel
StoryMessageModel.location_id: Mapped[str | None] = mapped_column(ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
StoryMessageModel.location = relationship("LocationModel")


class WorldviewSettingModel(Base):
    __tablename__ = "worldview_settings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_generate_id)
    story_id: Mapped[str] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"), index=True, nullable=False)
    term: Mapped[str] = mapped_column(String(length=255), nullable=False)
    nature: Mapped[str] = mapped_column(String(length=100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    source: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

    story: Mapped["StoryModel"] = relationship("StoryModel", back_populates="worldview_settings")


# Add relationship to StoryModel
StoryModel.worldview_settings = relationship("WorldviewSettingModel", back_populates="story", cascade="all, delete-orphan", order_by="WorldviewSettingModel.created_at")
