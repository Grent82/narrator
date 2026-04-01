from __future__ import annotations

import os

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings


def get_chat_model() -> ChatOllama:
    return ChatOllama(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b"),
    )


def get_story_generator_model() -> ChatOllama:
    return ChatOllama(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("STORY_GEN_MODEL", os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b")),
        temperature=float(os.getenv("STORY_GEN_TEMPERATURE", "0.85")),
        top_p=float(os.getenv("STORY_GEN_TOP_P", "0.92")),
        top_k=int(os.getenv("STORY_GEN_TOP_K", "60")),
        repeat_penalty=float(os.getenv("STORY_GEN_REPEAT_PENALTY", "1.05")),
        presence_penalty=float(os.getenv("STORY_GEN_PRESENCE_PENALTY", "0.3")),
        frequency_penalty=float(os.getenv("STORY_GEN_FREQUENCY_PENALTY", "0.25")),
    )


def get_story_generator_repair_model() -> ChatOllama:
    return ChatOllama(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("STORY_GEN_REPAIR_MODEL", os.getenv("STORY_GEN_MODEL", os.getenv("OLLAMA_MODEL", "dolphin-llama3:8b"))),
        temperature=float(os.getenv("STORY_GEN_REPAIR_TEMPERATURE", "0.2")),
        top_p=float(os.getenv("STORY_GEN_REPAIR_TOP_P", "0.95")),
        top_k=int(os.getenv("STORY_GEN_REPAIR_TOP_K", "40")),
        repeat_penalty=float(os.getenv("STORY_GEN_REPAIR_REPEAT_PENALTY", "1.05")),
    )


def get_embedding_model() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
    )
