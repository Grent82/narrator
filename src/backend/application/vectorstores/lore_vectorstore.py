from __future__ import annotations

import inspect
import logging
import os
from typing import Iterable, List

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

logger = logging.getLogger("backend")


class LoreVectorStore(VectorStore):
    def __init__(
        self,
        embeddings: Embeddings,
        story_id: str,
        client: QdrantClient | None = None,
        collection: str | None = None,
        vector_size: int | None = None,
    ) -> None:
        self._embeddings = embeddings
        self._story_id = story_id
        self._client = client or QdrantClient(url=os.getenv("QDRANT_URL", "http://qdrant:6333"))
        self._collection = collection or os.getenv("QDRANT_COLLECTION", "lore_vectors")
        self._vector_size = vector_size or int(os.getenv("EMBED_DIM", "768"))
        self._ensure_collection()

    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:
        return [doc for doc, _ in self.similarity_search_with_score(query, k, **kwargs)]

    def similarity_search_with_score(self, query: str, k: int = 4, **kwargs):
        if not query:
            return []
        query_vector = self._embeddings.embed_query(query)
        hits = self._search_points(query_vector, k)
        logger.debug("lore_qdrant_search query_len=%d hits=%d", len(query), len(hits))
        results = []
        for hit in hits:
            payload = hit.payload or {}
            content = str(payload.get("content", "") or "")
            metadata = dict(payload.get("metadata", {}) or {})
            logger.debug( "lore_qdrant_hit title=%s score=%.4f content_len=%d", metadata.get("title", ""), float(hit.score or 0.0), len(content), )
            results.append((Document(page_content=content, metadata=metadata), float(hit.score or 0.0)))
        return results

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
        points: list[PointStruct] = []
        ids: list[str] = []
        for idx, text in enumerate(text_list):
            metadata = (metadatas or [{}])[idx] if metadatas else {}
            lore_id = str(metadata.get("lore_id", "")) or None
            payload = {
                "story_id": self._story_id,
                "content": text,
                "metadata": metadata,
            }
            points.append(PointStruct(id=lore_id, vector=embeddings[idx], payload=payload))
            if lore_id:
                ids.append(lore_id)
        self._client.upsert(collection_name=self._collection, points=points)
        return ids

    def delete_by_lore_id(self, lore_id: str) -> None:
        if not lore_id:
            return
        self._client.delete(collection_name=self._collection, points_selector=[lore_id])

    def upsert_lore(self, lore_id: str, vector: list[float], payload: dict) -> None:
        if not lore_id:
            return
        point = PointStruct(id=lore_id, vector=vector, payload=payload)
        self._client.upsert(collection_name=self._collection, points=[point])

    @classmethod
    def from_texts(cls, texts: List[str], embedding: Embeddings, **kwargs):
        raise NotImplementedError("Use LoreVectorStore with an existing Qdrant collection")

    def _ensure_collection(self) -> None:
        try:
            info = self._client.get_collection(self._collection)
            size = info.config.params.vectors.size  # type: ignore[attr-defined]
            if size != self._vector_size:
                logger.warning(
                    "qdrant_collection_size_mismatch collection=%s expected=%d actual=%d",
                    self._collection,
                    self._vector_size,
                    size,
                )
            return
        except Exception:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    def _search_points(self, query_vector: list[float], limit: int):
        query_filter = self._story_filter()
        if hasattr(self._client, "search"):
            return self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
                with_payload=True,
            )
        if hasattr(self._client, "search_points"):
            fn = self._client.search_points
            kwargs = {
                "collection_name": self._collection,
                "query_vector": query_vector,
                "limit": limit,
                "with_payload": True,
            }
            sig = inspect.signature(fn)
            if "query_filter" in sig.parameters:
                kwargs["query_filter"] = query_filter
            elif "filter" in sig.parameters:
                kwargs["filter"] = query_filter
            return fn(**kwargs)
        if hasattr(self._client, "query_points"):
            fn = self._client.query_points
            kwargs = {
                "collection_name": self._collection,
                "limit": limit,
                "with_payload": True,
            }
            sig = inspect.signature(fn)
            if "query_vector" in sig.parameters:
                kwargs["query_vector"] = query_vector
            elif "query" in sig.parameters:
                kwargs["query"] = query_vector
            if "query_filter" in sig.parameters:
                kwargs["query_filter"] = query_filter
            elif "filter" in sig.parameters:
                kwargs["filter"] = query_filter
            result = fn(**kwargs)
            return getattr(result, "points", getattr(result, "result", result))
        raise RuntimeError("Qdrant client does not support vector search")

    def _story_filter(self) -> Filter:
        return Filter(must=[FieldCondition(key="story_id", match=MatchValue(value=self._story_id))])
