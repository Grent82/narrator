from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

from langchain_core.documents import Document

from src.backend.application.ports import EmbeddingsProtocol
from src.backend.application.vectorstores.lore_vectorstore import LoreVectorStore


class LoreRepository(Protocol):
    def retrieve(self, story_id: str, query: str) -> list[Document]:
        ...


@dataclass
class DbLoreRepository:
    embeddings: EmbeddingsProtocol

    def retrieve(self, story_id: str, query: str) -> list[Document]:
        top_k = int(os.getenv("LORE_TOP_K", "8"))
        store = LoreVectorStore(self.embeddings, story_id)
        return store.similarity_search(query, k=top_k)
