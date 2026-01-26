from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.backend.infrastructure.models import StoryModel


class StoryRepository(Protocol):
    def get_story(self, story_id: str) -> StoryModel | None:
        ...

    def commit(self) -> None:
        ...


@dataclass
class DbStoryRepository:
    db: object

    def get_story(self, story_id: str) -> StoryModel | None:
        return self.db.query(StoryModel).filter(StoryModel.id == story_id).first()

    def commit(self) -> None:
        self.db.commit()
