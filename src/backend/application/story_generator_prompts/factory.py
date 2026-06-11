"""Factory for creating story generator prompt strategies."""

from __future__ import annotations

from typing import Literal

from src.backend.application.size_tier import SizeProfile
from src.backend.application.story_generator_prompts.base import (
    StoryGeneratorStrategy,
)
from src.backend.application.story_generator_prompts.claude import (
    ClaudeGeneratorStrategy,
)
from src.backend.application.story_generator_prompts.llama import (
    LlamaGeneratorStrategy,
)
from src.backend.application.story_generator_prompts.qwen import (
    QwenGeneratorStrategy,
)

Provider = Literal["ollama", "openai_compatible", "anthropic", "qwen", "auto"]


# Strategy mapping by provider
STRATEGY_MAP: dict[str, type[StoryGeneratorStrategy]] = {
    "anthropic": ClaudeGeneratorStrategy,
    "claude": ClaudeGeneratorStrategy,
    "qwen": QwenGeneratorStrategy,
    "ollama": LlamaGeneratorStrategy,
    "llama": LlamaGeneratorStrategy,
    "dolphin": LlamaGeneratorStrategy,
    "mistral": LlamaGeneratorStrategy,
    "mixtral": LlamaGeneratorStrategy,
}

# Provider override mapping
PROVIDER_STRATEGY_MAP: dict[Provider, type[StoryGeneratorStrategy]] = {
    "anthropic": ClaudeGeneratorStrategy,
    "qwen": QwenGeneratorStrategy,
    "ollama": LlamaGeneratorStrategy,
    "openai_compatible": LlamaGeneratorStrategy,
    "auto": LlamaGeneratorStrategy,
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


def get_generator_strategy(
    model_name: str | None = None,
    provider: Provider = "auto",
    size_profile: SizeProfile | None = None,
) -> StoryGeneratorStrategy:
    """Get the appropriate generator strategy for a model.

    Args:
        model_name: The model identifier
        provider: Explicit provider override ("auto" to detect from model_name)
        size_profile: Pre-computed size profile

    Returns:
        An instantiated StoryGeneratorStrategy appropriate for the model
    """
    from src.backend.application.size_tier import get_size_profile

    # Determine provider
    if provider == "auto":
        if model_name:
            provider = detect_provider_from_model_name(model_name)
        else:
            provider = "ollama"

    # Get size profile if not provided
    if size_profile is None:
        size_profile = get_size_profile(model_name)

    # Select strategy class
    strategy_class: type[StoryGeneratorStrategy]

    if provider in PROVIDER_STRATEGY_MAP:
        strategy_class = PROVIDER_STRATEGY_MAP[provider]
    elif model_name:
        normalized = model_name.lower()
        for pattern, strat in STRATEGY_MAP.items():
            if pattern in normalized:
                strategy_class = strat
                break
        else:
            strategy_class = LlamaGeneratorStrategy
    else:
        strategy_class = LlamaGeneratorStrategy

    return strategy_class(size_profile=size_profile)


def list_available_strategies() -> dict[str, str]:
    """List all available generator strategies.

    Returns:
        Dictionary mapping provider names to descriptions
    """
    return {
        "anthropic": "Claude models using XML formatting",
        "qwen": "Qwen models using Markdown formatting",
        "ollama": "Ollama models (Llama, Dolphin, etc.) using Markdown",
        "auto": "Auto-detect provider from model name",
    }
