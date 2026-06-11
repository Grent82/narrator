"""Provider-specific prompt strategies for story generation.

This package contains strategy implementations for different LLM providers
specifically for the story generation use case (world-building JSON output).

Each strategy handles:
- Provider-specific prompt formatting (XML vs Markdown)
- Model-size adapted guidance
- JSON output instructions
"""

from src.backend.application.story_generator_prompts.base import (
    GeneratorContext,
    StoryGeneratorStrategy,
)
from src.backend.application.story_generator_prompts.factory import (
    get_generator_strategy,
    list_available_strategies,
    detect_provider_from_model_name,
)

__all__ = [
    "GeneratorContext",
    "StoryGeneratorStrategy",
    "get_generator_strategy",
    "list_available_strategies",
    "detect_provider_from_model_name",
]
