"""Factory for selecting and creating prompt strategies.

This module provides the central factory that selects the appropriate
prompt strategy based on model name, provider, and configuration.
"""

from __future__ import annotations

from typing import Literal

from src.backend.application.prompt_strategies.base import PromptStrategy
from src.backend.application.prompt_strategies.claude import ClaudePromptStrategy
from src.backend.application.prompt_strategies.llama import LlamaPromptStrategy
from src.backend.application.prompt_strategies.qwen import QwenPromptStrategy
from src.backend.application.size_tier import SizeProfile, get_size_profile

Provider = Literal["ollama", "openai_compatible", "anthropic", "qwen", "auto"]


# Mapping from provider/model tokens to strategy types
STRATEGY_MAP: dict[str, type[PromptStrategy]] = {
    "anthropic": ClaudePromptStrategy,
    "claude": ClaudePromptStrategy,
    "qwen": QwenPromptStrategy,
    "ollama": LlamaPromptStrategy,
    "llama": LlamaPromptStrategy,
    "dolphin": LlamaPromptStrategy,
    "mistral": LlamaPromptStrategy,
    "mixtral": LlamaPromptStrategy,
}

# Provider override mapping - explicit provider selection
PROVIDER_STRATEGY_MAP: dict[Provider, type[PromptStrategy]] = {
    "anthropic": ClaudePromptStrategy,
    "qwen": QwenPromptStrategy,
    "ollama": LlamaPromptStrategy,
    "openai_compatible": LlamaPromptStrategy,  # Default for unknown remote models
    "auto": LlamaPromptStrategy,  # Auto-detect default
}


def detect_provider_from_model_name(model_name: str) -> str:
    """Detect provider from model name.

    Args:
        model_name: The model identifier (e.g., "anthropic/claude-sonnet", "qwen/qwen-2.5")

    Returns:
        Detected provider name
    """
    normalized = model_name.lower()

    # Check for explicit provider prefixes
    if normalized.startswith("anthropic/") or "claude" in normalized:
        return "anthropic"
    if normalized.startswith("qwen/") or normalized.startswith("qwen-"):
        return "qwen"
    if normalized.startswith("ollama/") or normalized.startswith("dolphin-"):
        return "ollama"

    # Check for known model patterns
    for pattern, provider in [
        ("llama", "ollama"),
        ("mistral", "ollama"),
        ("mixtral", "ollama"),
        ("phi", "ollama"),
        ("gemma", "ollama"),
    ]:
        if pattern in normalized:
            return provider

    # Default to ollama-style for unknown models
    return "ollama"


def get_prompt_strategy(
    model_name: str | None = None,
    provider: Provider = "auto",
    size_profile: SizeProfile | None = None,
) -> PromptStrategy:
    """Get the appropriate prompt strategy for a model.

    Args:
        model_name: The model identifier (e.g., "dolphin-llama3:8b", "anthropic/claude-sonnet")
        provider: Explicit provider override ("auto" to detect from model_name)
        size_profile: Optional pre-computed size profile

    Returns:
        An instantiated PromptStrategy appropriate for the model
    """
    # Determine provider
    if provider == "auto":
        if model_name:
            provider = detect_provider_from_model_name(model_name)
        else:
            provider = "ollama"  # Default

    # Get size profile if not provided
    if size_profile is None:
        size_profile = get_size_profile(model_name)

    # Select strategy class
    strategy_class: type[PromptStrategy]

    # First check explicit provider mapping
    if provider in PROVIDER_STRATEGY_MAP:
        strategy_class = PROVIDER_STRATEGY_MAP[provider]
    # Then check model-name based detection
    elif model_name:
        normalized = model_name.lower()
        for pattern, strat in STRATEGY_MAP.items():
            if pattern in normalized:
                strategy_class = strat
                break
        else:
            strategy_class = LlamaPromptStrategy  # Default
    else:
        strategy_class = LlamaPromptStrategy  # Default

    return strategy_class(size_profile=size_profile)


def get_strategy_for_provider(provider: Provider) -> type[PromptStrategy]:
    """Get the strategy class for a provider (without instantiation).

    Args:
        provider: The provider name

    Returns:
        The PromptStrategy class for that provider
    """
    return PROVIDER_STRATEGY_MAP.get(provider, LlamaPromptStrategy)


def list_available_strategies() -> dict[str, str]:
    """List all available strategies and their purposes.

    Returns:
        Dictionary mapping provider names to descriptions
    """
    return {
        "anthropic": "Claude models using XML formatting (Claude 3.x, Sonnet, Opus)",
        "qwen": "Qwen models using Markdown formatting (Qwen 2.5, Qwen-Coder)",
        "ollama": "Ollama models using Markdown (Llama, Dolphin, Mistral, etc.)",
        "auto": "Auto-detect provider from model name",
    }
