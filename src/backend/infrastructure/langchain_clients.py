from __future__ import annotations

import os

from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings

from src.backend.application.ports import ChatModelProtocol
from src.backend.infrastructure.llm_config import (
    active_chat_model_name,
    active_story_generator_model_name,
    active_story_generator_repair_model_name,
    get_chat_model_config,
)
from src.backend.infrastructure.openai_compatible_client import OpenAICompatibleChatModel


def _build_chat_model(model: str | None = None, **options) -> ChatModelProtocol:
    config = get_chat_model_config(model)
    if config.provider == "openai_compatible":
        client = OpenAICompatibleChatModel(
            base_url=config.base_url,
            model=config.model,
            api_key=config.api_key,
        )
        return client.bind(**options) if options else client
    return ChatOllama(
        base_url=config.base_url,
        model=config.model,
        **options,
    )


def get_chat_model() -> ChatModelProtocol:
    return _build_chat_model(active_chat_model_name())


def get_story_generator_model() -> ChatModelProtocol:
    return _build_chat_model(
        active_story_generator_model_name(),
        temperature=float(os.getenv("STORY_GEN_TEMPERATURE", "0.85")),
        top_p=float(os.getenv("STORY_GEN_TOP_P", "0.92")),
        top_k=int(os.getenv("STORY_GEN_TOP_K", "60")),
        repeat_penalty=float(os.getenv("STORY_GEN_REPEAT_PENALTY", "1.05")),
        presence_penalty=float(os.getenv("STORY_GEN_PRESENCE_PENALTY", "0.3")),
        frequency_penalty=float(os.getenv("STORY_GEN_FREQUENCY_PENALTY", "0.25")),
    )


def get_story_generator_repair_model() -> ChatModelProtocol:
    return _build_chat_model(
        active_story_generator_repair_model_name(),
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
