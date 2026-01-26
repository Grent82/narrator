from __future__ import annotations

from dataclasses import dataclass

from src.backend.infrastructure.models import LoreEntryModel, StoryModel


@dataclass(frozen=True)
class TurnPayload:
    text: str | None = None
    mode: str | None = None
    story_id: str | None = None
    trigger: str | None = None


@dataclass
class TurnContext:
    text: str
    mode: str
    story: StoryModel | None
    lore_entries: list[LoreEntryModel] | None
