from __future__ import annotations

import os

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings


def get_chat_model() -> ChatOllama:
    return ChatOllama(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b"),
    )


def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
    )
