from __future__ import annotations

from typing import Iterable, List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from sqlalchemy.orm import Session

from src.backend.infrastructure.models import LoreVectorModel


class LoreVectorStore(VectorStore):
    def __init__(self, db: Session, embeddings: Embeddings, story_id: str) -> None:
        self._db = db
        self._embeddings = embeddings
        self._story_id = story_id

    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:
        base_query = self._db.query(LoreVectorModel).filter(LoreVectorModel.story_id == self._story_id)
        if query:
            embedding = self._embeddings.embed_query(query)
            results = (
                base_query.filter(LoreVectorModel.embedding.isnot(None))
                .order_by(LoreVectorModel.embedding.cosine_distance(embedding))
                .limit(k)
                .all()
            )
            if results:
                return [Document(page_content=row.content, metadata=dict(row.metadata_ or {})) for row in results]
        fallback = base_query.order_by(LoreVectorModel.created_at.desc()).limit(k).all()
        return [Document(page_content=row.content, metadata=dict(row.metadata_ or {})) for row in fallback]

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        base_query = self._db.query(LoreVectorModel).filter(LoreVectorModel.story_id == self._story_id)
        if query:
            embedding = self._embeddings.embed_query(query)
            results = (
                base_query.filter(LoreVectorModel.embedding.isnot(None))
                .order_by(LoreVectorModel.embedding.cosine_distance(embedding))
                .limit(k)
                .all()
            )
            if results:
                return [
                    (Document(page_content=row.content, metadata=dict(row.metadata_ or {})), 0.0)
                    for row in results
                ]
        fallback = base_query.order_by(LoreVectorModel.created_at.desc()).limit(k).all()
        return [(Document(page_content=row.content, metadata=dict(row.metadata_ or {})), 0.0) for row in fallback]

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: List[dict] | None = None,
        **kwargs,
    ) -> List[str]:
        text_list = list(texts)
        if not text_list:
            return []
        embeddings = self._embeddings.embed_documents(text_list)
        ids = []
        for idx, text in enumerate(text_list):
            metadata = (metadatas or [{}])[idx] if metadatas else {}
            lore_id = str(metadata.get("lore_id", ""))
            row = LoreVectorModel(
                story_id=self._story_id,
                lore_id=lore_id,
                content=text,
                metadata_=metadata,
                embedding=embeddings[idx] if idx < len(embeddings) else None,
            )
            self._db.add(row)
            self._db.flush()
            ids.append(row.id)
        return ids

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, **kwargs):
        raise NotImplementedError("Use LoreVectorStore with an existing Session and story_id")
