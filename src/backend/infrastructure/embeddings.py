import os
from typing import List, Optional

from ollama import Client as OllamaClient


def _get_embed_model() -> str:
    return os.getenv("EMBED_MODEL", "nomic-embed-text")


def _normalize_embeddings(response: dict) -> Optional[List[float]]:
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
    response = ollama.embed(model=model, input=text)
    return _normalize_embeddings(response)


def build_lore_text(title: str, tag: str, triggers: str, description: str) -> str:
    parts = [title.strip(), tag.strip(), triggers.strip(), description.strip()]
    return "\n".join(part for part in parts if part)
