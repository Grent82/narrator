from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.backend.application.ports import OllamaProtocol

from src.backend.application.lore_retrieval import retrieve_relevant_lore
from src.backend.infrastructure.models import LoreEntryModel


class LoreRepository(Protocol):
    def retrieve(self, story_id: str, query: str, ollama: OllamaProtocol) -> list[LoreEntryModel]:
        ...


@dataclass
class DbLoreRepository:
    db: object

    def retrieve(self, story_id: str, query: str, ollama: OllamaProtocol) -> list[LoreEntryModel]:
        return retrieve_relevant_lore(self.db, story_id, query, ollama)
