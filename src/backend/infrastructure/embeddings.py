import logging
import os
from typing import List, Optional

from ollama import Client as OllamaClient

logger = logging.getLogger("backend.embeddings")


def _get_embed_model() -> str:
    return os.getenv("EMBED_MODEL", "nomic-embed-text")


def _normalize_embeddings(response: object) -> Optional[List[float]]:
    if response is None:
        return None
    if hasattr(response, "model_dump"):
        try:
            return _normalize_embeddings(response.model_dump())
        except Exception:
            return None
    if hasattr(response, "embedding"):
        embedding = getattr(response, "embedding")
        if isinstance(embedding, list):
            return embedding
    if hasattr(response, "embeddings"):
        embeddings = getattr(response, "embeddings")
        if isinstance(embeddings, list) and embeddings:
            first = embeddings[0]
            if isinstance(first, list):
                return first
    if not isinstance(response, dict):
        return None
    if "embedding" in response and isinstance(response["embedding"], list):
        return response["embedding"]
    embeddings = response.get("embeddings")
    if isinstance(embeddings, list) and embeddings:
        first = embeddings[0]
        if isinstance(first, list):
            return first
    return None


def embed_text(ollama: OllamaClient, text: str) -> Optional[List[float]]:
    model = _get_embed_model()
    try:
        response = ollama.embed(model=model, input=text)
        embedding = _normalize_embeddings(response)
        if embedding is None:
            logger.warning("embed_parse_failed model=%s response_type=%s", model, type(response))
            if hasattr(response, "model_dump"):
                try:
                    data = response.model_dump()
                    logger.warning("embed_parse_failed_keys model=%s keys=%s", model, list(data.keys()))
                except Exception:
                    pass
            elif isinstance(response, dict):
                logger.warning("embed_parse_failed_keys model=%s keys=%s", model, list(response.keys()))
        return embedding
    except Exception as exc:
        logger.warning("embed_failed using /api/embed, trying /api/embeddings: %s", exc)
        try:
            response = ollama.embeddings(model=model, prompt=text)
            embedding = _normalize_embeddings(response)
            if embedding is None and isinstance(response, dict):
                logger.warning("embed_fallback_parse_failed model=%s keys=%s", model, list(response.keys()))
            return embedding
        except Exception as exc2:
            logger.warning("embed_fallback_failed: %s", exc2)
            return None
