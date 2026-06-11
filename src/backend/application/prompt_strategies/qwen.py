"""Qwen-specific prompt strategy using Markdown formatting.

Qwen models respond well to Markdown-structured prompts similar to GPT models.
This strategy implements:
- Markdown-based prompt structure
- Model-size adapted guidance with CoT for smaller models
- Clear section headers and formatting
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.backend.application.prompt_strategies.base import PromptContext, PromptStrategy
from src.backend.application.size_tier import SizeProfile, get_size_profile


class QwenPromptStrategy(PromptStrategy):
    """Strategy for Qwen models using Markdown formatting."""

    def __init__(self, size_profile: SizeProfile | None = None):
        super().__init__(size_profile or get_size_profile(None))

    @property
    def provider_name(self) -> str:
        return "qwen"

    def build_system_prompt(self, context: PromptContext) -> str:
        """Build Qwen-formatted system prompt with Markdown structure."""
        sections = []

        # Role definition
        role = self._build_role(context.mode)
        sections.append(role)

        # AI Instructions
        if context.ai_instructions:
            sections.append(f"## AI Instructions\n\n{context.ai_instructions}")

        # Plot Summary
        if context.plot_summary:
            sections.append(f"## Plot Summary\n\n{context.plot_summary}")

        # Plot Essentials
        if context.plot_essentials:
            sections.append(f"## Plot Essentials\n\n{context.plot_essentials}")

        # Lore
        if context.lore_block:
            sections.append(f"## Lore\n\n{context.lore_block}")

        # Worldview Settings
        if context.worldview_block:
            sections.append(f"## Worldview Settings\n\n{context.worldview_block}")

        # Author Note
        if context.author_note:
            sections.append(f"## Author Note\n\n{context.author_note}")

        # Model-specific guidance (from existing profile system)
        if context.model_profile_id:
            from src.backend.application.prompt_renderer import (
                render_profile_guidance,
            )

            profile_guidance = render_profile_guidance(
                context.model_profile_id, context.mode
            )
            if profile_guidance:
                sections.append(f"## Model Guidance\n\n{profile_guidance}")

        # Size-adapted guidance
        size_guidance = self._build_size_guidance(context)
        if size_guidance:
            sections.append(size_guidance)

        # Core task
        task = self._build_task(context.mode)
        sections.append(task)

        return "\n\n".join(sections)

    def _build_role(self, mode: str) -> str:
        """Build role definition."""
        if mode == "continue":
            return """# Role

You are a skilled narrative continuist. Your task is to continue stories seamlessly from the exact endpoint of the last response, without repeating or restating any content."""
        return """# Role

You are an immersive dark fantasy narrator. You tell stories in a grim, atmospheric style reminiscent of Joe Abercrombie, early George R.R. Martin, and FromSoftware lore. Your narratives are morally gray, grounded, and unsettling."""

    def _build_size_guidance(self, context: PromptContext) -> str:
        """Build size-adapted guidance in Markdown format."""
        if not self.size_profile:
            return ""

        parts = []

        # Verbosity guidance
        if self.size_profile.verbosity == "compact":
            parts.append(
                "## Response Style\n\n"
                "Keep responses concise and focused. Follow instructions literally."
            )
        elif self.size_profile.verbosity == "elaborate":
            parts.append(
                "## Response Style\n\n"
                "Provide thorough, detailed responses. Explore nuances and implications."
            )

        # CoT guidance for small models
        if self.size_profile.require_cot:
            if self.size_profile.cot_style == "explicit_tags":
                if context.mode == "continue":
                    parts.append(
                        "## Thinking Process\n\n"
                        "Before continuing, analyze:\n"
                        "1. The exact endpoint of the last assistant message\n"
                        "2. What naturally follows without repetition\n"
                        "3. How to maintain seamless continuity\n\n"
                        "Write your reasoning first, then provide the continuation."
                    )
                else:
                    parts.append(
                        "## Thinking Process\n\n"
                        "Before responding, think through:\n"
                        "1. Current situation and character state\n"
                        "2. Consequences of the player's action\n"
                        "3. The most interesting logical next beat\n\n"
                        "Write your reasoning first, then provide the story response."
                    )
            elif self.size_profile.cot_style == "implicit":
                if context.mode == "continue":
                    parts.append(
                        "## Step-by-Step Thinking\n\n"
                        "Think through before writing:\n"
                        "- What is the exact endpoint of the last response?\n"
                        "- What is the immediate next beat that follows?\n"
                        "- How do you continue without repeating or restating?\n\n"
                        "Write your reasoning, then provide the continuation."
                    )
                else:
                    parts.append(
                        "## Step-by-Step Thinking\n\n"
                        "Think through before responding:\n"
                        "- What is the current situation?\n"
                        "- What does the player's action trigger?\n"
                        "- What is the most interesting but logical next beat?\n\n"
                        "Write your reasoning, then provide the story response."
                    )

        # Repetition prevention
        if self.size_profile.repetition_risk in ("very_high", "high"):
            parts.append(
                "## Avoid Repetition\n\n"
                "CRITICAL: You tend to repeat yourself. Follow these rules strictly:\n"
                "- Do NOT copy any sentences from previous assistant messages\n"
                "- Do NOT rephrase or paraphrase prior text\n"
                "- Do NOT restart scenes or reset character states\n"
                "- Do NOT use similar closing lines repeatedly\n"
                "- Each response must add NEW content, not restate old content"
            )
        elif self.size_profile.repetition_risk == "medium":
            parts.append(
                "## Be Mindful of Repetition\n\n"
                "- Add new content rather than restating\n"
                "- Vary your phrasing and vocabulary"
            )

        # Few-shot examples for tiny/small models
        if self.size_profile.include_few_shot:
            parts.append(self._build_few_shot_examples(context.mode))

        return "\n\n".join(parts) if parts else ""

    def _build_few_shot_examples(self, mode: str) -> str:
        """Build few-shot examples for small models."""
        if mode == "continue":
            return """## Examples

### Good Continuation
**Last Assistant:** The door creaked open, revealing a dimly lit chamber beyond.
**Continuation:** Footsteps echoed on stone as you crossed the threshold. The air grew colder, carrying the scent of mildew and something metallic. In the corner, a shadow shifted—too deliberate to be natural.

### Bad Continuation
**Last Assistant:** The door creaked open, revealing a dimly lit chamber beyond.
**Continuation:** The door creaked open slowly. You saw a chamber that was dimly lit. It was dark inside.

---

Remember: Continue from where the last response ended. Do not repeat or restate."""
        return """## Examples

### Good Response
**User:** I examine the ancient sword on the wall.
**Assistant:** The blade is rusted but the hilt remains ornate—gold inlay depicting a crown broken in three places. A name is etched near the base: "Vorthas the Usurper."

### Bad Response
**User:** I examine the ancient sword on the wall.
**Assistant:** You look at the sword. It is old and on the wall. The sword looks rusty.

---

Remember: Add new information. Be specific. Avoid generic descriptions."""

    def _build_task(self, mode: str) -> str:
        """Build task definition."""
        if mode == "continue":
            return """## Task

Continue the story from the exact endpoint of the last assistant message.

### Rules
- Do not repeat, paraphrase, restart, or summarize prior text
- Write only new narrative progression
- Maintain consistent tone and style
- Advance the scene naturally"""
        return """## Task

Respond to the player's action as an immersive dark fantasy narrator.

### Rules
- Preserve story state, character intent, and consequences
- Advance the current scene without contradicting summary, lore, or recent turns
- Keep tone consistent while avoiding repetitive phrasing
- Introduce concrete developments: state changes, discoveries, conflicts, decisions"""

    def build_messages(
        self,
        context: PromptContext,
    ) -> list[BaseMessage]:
        """Build Qwen-formatted message list."""
        messages: list[BaseMessage] = []

        # System prompt
        system_prompt = self.build_system_prompt(context)
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # History messages
        if context.recent_messages:
            for msg in context.recent_messages:
                if isinstance(msg, HumanMessage):
                    messages.append(msg)
                elif isinstance(msg, AIMessage):
                    messages.append(msg)

        # Current user input
        if context.user_text:
            formatted_input = self._format_user_input(context.mode, context.user_text)
            messages.append(HumanMessage(content=formatted_input))

        return messages

    def _format_user_input(self, mode: str, text: str) -> str:
        """Format user input with mode indicator."""
        mode_labels = {
            "story": "STORY",
            "say": "SAY",
            "do": "DO",
            "continue": "CONTINUE",
        }
        mode_label = mode_labels.get(mode, mode.upper())
        return f"MODE: {mode_label}\nTEXT: {text}"
