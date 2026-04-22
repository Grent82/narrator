from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

ChatProvider = Literal["ollama", "openai_compatible"]

DEFAULT_OLLAMA_MODEL = "dolphin-llama3:8b"


@dataclass(frozen=True)
class ChatModelConfig:
    provider: ChatProvider
    base_url: str
    model: str
    api_key: str | None = None
    timeout: float = 30.0
    enable_thinking: bool | None = None


def _env_first(*keys: str) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value and value.strip():
            return value.strip()
    return None


def _provider() -> ChatProvider:
    provider = (_env_first("LLM_PROVIDER") or "ollama").lower()
    if provider in {"openai", "openai-compatible", "openai_compatible", "ai_hub", "hub"}:
        return "openai_compatible"
    return "ollama"


def _optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def active_provider_name() -> ChatProvider:
    return _provider()


def active_chat_model_name() -> str:
    return _env_first("LLM_MODEL", "OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL


def active_summary_model_name() -> str:
    return _env_first("SUMMARY_MODEL") or active_chat_model_name()


def active_story_generator_model_name() -> str:
    return _env_first("STORY_GEN_MODEL") or active_chat_model_name()


def active_story_generator_repair_model_name() -> str:
    return _env_first("STORY_GEN_REPAIR_MODEL") or active_story_generator_model_name()


def get_chat_model_config(model: str | None = None) -> ChatModelConfig:
    provider = _provider()
    resolved_model = model or active_chat_model_name()
    if provider == "openai_compatible":
        base_url = _env_first(
            "LLM_BASE_URL",
            "OPENAI_COMPATIBLE_BASE_URL",
            "AI_HUB_BASE_URL",
        )
        if not base_url:
            raise RuntimeError("LLM_PROVIDER=openai_compatible requires LLM_BASE_URL")
        return ChatModelConfig(
            provider=provider,
            base_url=base_url,
            model=resolved_model,
            api_key=_env_first("LLM_API_KEY", "OPENAI_API_KEY", "AI_HUB_API_KEY"),
            timeout=float(_env_first("LLM_TIMEOUT_SECONDS") or "30"),
            enable_thinking=_optional_bool(_env_first("LLM_ENABLE_THINKING")),
        )
    return ChatModelConfig(
        provider=provider,
        base_url=_env_first("OLLAMA_URL") or "http://localhost:11434",
        model=resolved_model,
    )
