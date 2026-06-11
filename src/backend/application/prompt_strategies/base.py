"""Abstract base class for prompt strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import BaseMessage

from src.backend.application.size_tier import SizeProfile


@dataclass
class PromptContext:
    """Context data for prompt rendering."""
    # Story data
    ai_instructions: str | None = None
    plot_summary: str | None = None
    plot_essentials: str | None = None
    lore_block: str | None = None
    author_note: str | None = None

    # Mode and configuration
    mode: str = "story"
    model_profile_id: str | None = None
    model_name: str | None = None

    # History
    recent_messages: list[BaseMessage] | None = None

    # Current user input
    user_text: str = ""

    # Additional context
    extra_context: dict[str, Any] | None = None


class PromptStrategy(ABC):
    """Abstract base class for provider-specific prompt strategies.

    Subclasses implement:
    - Provider-specific formatting (XML, Markdown, etc.)
    - Template selection and rendering
    - Size-adapted guidance injection
    """

    def __init__(self, size_profile: SizeProfile | None = None):
        """Initialize the strategy.

        Args:
            size_profile: Optional size profile for model-size adaptations
        """
        self.size_profile = size_profile

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name this strategy handles."""
        ...

    @abstractmethod
    def build_system_prompt(self, context: PromptContext) -> str:
        """Build the system prompt for a turn.

        Args:
            context: The prompt context with all relevant data

        Returns:
            The formatted system prompt string
        """
        ...

    @abstractmethod
    def build_messages(
        self,
        context: PromptContext,
    ) -> list[BaseMessage]:
        """Build the full message list for a turn.

        Args:
            context: The prompt context with all relevant data

        Returns:
            List of LangChain messages ready for the LLM
        """
        ...

    def inject_size_guidance(self, base_prompt: str, context: PromptContext) -> str:
        """Inject size-adapted guidance into the prompt.

        Args:
            base_prompt: The base prompt to enhance
            context: The prompt context

        Returns:
            Enhanced prompt with size-adapted guidance
        """
        from src.backend.application.size_tier import (
            get_cot_instructions,
            get_repetition_prevention_guidance,
        )

        if not self.size_profile:
            return base_prompt

        # Add CoT guidance for small models
        cot_guidance = get_cot_instructions(context.model_name, context.mode)
        if cot_guidance:
            base_prompt = base_prompt + cot_guidance

        # Add repetition prevention for high-risk models
        if self.size_profile.repetition_risk in ("very_high", "high"):
            rep_guidance = get_repetition_prevention_guidance(context.model_name)
            if rep_guidance:
                base_prompt = base_prompt + rep_guidance

        return base_prompt

    def render_template(self, template_name: str, context: PromptContext) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template to render
            context: The prompt context

        Returns:
            Rendered template string
        """
        # Default implementation - subclasses override with template engine
        raise NotImplementedError("Template rendering not implemented")
