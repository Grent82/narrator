"""Abstract base class for story generator prompt strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.backend.application.size_tier import SizeProfile


@dataclass
class GeneratorContext:
    """Context data for story generation prompts.

    Contains all inputs needed to build a world-generation prompt.
    """
    ai_instruction_key: str
    role: str
    name: str
    gender: str
    age: str
    traits: str
    world_input: str
    start_template: str
    start_custom: str
    size_profile: SizeProfile


class StoryGeneratorStrategy(ABC):
    """Abstract base class for provider-specific story generation strategies.

    Each strategy implements provider-specific prompt formatting:
    - Claude: XML-based structure
    - Qwen: Markdown with section headers
    - Llama: Markdown with explicit task definitions

    All strategies produce prompts that instruct the model to output
    valid JSON for world/story generation.
    """

    def __init__(self, size_profile: SizeProfile):
        """Initialize the strategy.

        Args:
            size_profile: Size profile for model-adapted guidance
        """
        self.size_profile = size_profile

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name this strategy handles."""
        ...

    @abstractmethod
    def build_system_prompt(self, ctx: GeneratorContext) -> str:
        """Build the system prompt for story generation.

        Args:
            ctx: The generation context with all story inputs

        Returns:
            Formatted system prompt string
        """
        ...

    @abstractmethod
    def build_user_prompt(self, ctx: GeneratorContext) -> str:
        """Build the user prompt for story generation.

        Args:
            ctx: The generation context with all story inputs

        Returns:
            Formatted user prompt string
        """
        ...
