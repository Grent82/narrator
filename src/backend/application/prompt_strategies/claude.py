"""Claude-specific prompt strategy using XML formatting.

Anthropic recommends XML tags for structuring prompts to Claude models.
This strategy implements:
- XML-based prompt structure
- Model-size adapted guidance
- Thinking/prefill support for newer Claude versions
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.backend.application.prompt_strategies.base import PromptContext, PromptStrategy
from src.backend.application.size_tier import SizeProfile, get_size_profile


class ClaudePromptStrategy(PromptStrategy):
    """Strategy for Claude/Anthropic models using XML formatting."""

    def __init__(self, size_profile: SizeProfile | None = None):
        super().__init__(size_profile or get_size_profile(None))

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def build_system_prompt(self, context: PromptContext) -> str:
        """Build Claude-formatted system prompt with XML structure."""
        sections = []

        # AI Instructions
        if context.ai_instructions:
            sections.append(
                f"<ai_instructions>\n{context.ai_instructions}\n</ai_instructions>"
            )

        # Plot Summary
        if context.plot_summary:
            sections.append(
                f"<plot_summary>\n{context.plot_summary}\n</plot_summary>"
            )

        # Plot Essentials
        if context.plot_essentials:
            sections.append(
                f"<plot_essentials>\n{context.plot_essentials}\n</plot_essentials>"
            )

        # Lore
        if context.lore_block:
            sections.append(f"<lore>\n{context.lore_block}\n</lore>")

        # Worldview Settings
        if context.worldview_block:
            sections.append(
                f"<worldview_settings>\n{context.worldview_block}\n</worldview_settings>"
            )

        # Author Note
        if context.author_note:
            sections.append(
                f"<author_note>\n{context.author_note}\n</author_note>"
            )

        # Model-specific guidance (from existing profile system)
        if context.model_profile_id:
            from src.backend.application.prompt_renderer import (
                render_profile_guidance,
            )

            profile_guidance = render_profile_guidance(
                context.model_profile_id, context.mode
            )
            if profile_guidance:
                sections.append(
                    f"<model_guidance>\n{profile_guidance}\n</model_guidance>"
                )

        # Size-adapted guidance
        size_guidance = self._build_size_guidance(context)
        if size_guidance:
            sections.append(size_guidance)

        # Core instructions section
        core_instructions = self._build_core_instructions(context.mode)
        sections.append(core_instructions)

        # Output format - Thought/Speech/Action structure
        output_format = self._build_output_format_instructions(context.mode)
        sections.append(output_format)

        return "\n\n".join(sections)

    def _build_size_guidance(self, context: PromptContext) -> str:
        """Build size-adapted guidance in XML format."""
        if not self.size_profile:
            return ""

        parts = []

        # Verbosity guidance
        if self.size_profile.verbosity == "compact":
            parts.append(
                "<verbosity_guidance>\n"
                "Keep responses concise and focused. Follow instructions literally.\n"
                "</verbosity_guidance>"
            )
        elif self.size_profile.verbosity == "elaborate":
            parts.append(
                "<verbosity_guidance>\n"
                "Provide thorough, detailed responses. Explore nuances and implications.\n"
                "</verbosity_guidance>"
            )

        # CoT guidance for small models
        if self.size_profile.require_cot and self.size_profile.cot_style == "explicit_tags":
            if context.mode == "continue":
                parts.append(
                    "<thinking>\n"
                    "Before continuing, analyze:\n"
                    "1. The exact endpoint of the last assistant message\n"
                    "2. What naturally follows without repetition\n"
                    "3. How to maintain seamless continuity\n"
                    "</thinking>\n"
                    "<guidance>\n"
                    "Use your thinking block to plan, then write the continuation.\n"
                    "</guidance>"
                )
            else:
                parts.append(
                    "<thinking>\n"
                    "Before responding, think through:\n"
                    "1. Current situation and character state\n"
                    "2. Consequences of the player's action\n"
                    "3. The most interesting logical next beat\n"
                    "</thinking>\n"
                    "<guidance>\n"
                    "Use your thinking block to reason, then provide the story.\n"
                    "</guidance>"
                )

        # Repetition prevention
        if self.size_profile.repetition_risk in ("very_high", "high"):
            parts.append(
                "<repetition_prevention>\n"
                "CRITICAL: Avoid all forms of repetition:\n"
                "- Do not copy sentences from prior messages\n"
                "- Do not rephrase or restate previous content\n"
                "- Do not restart scenes or reset states\n"
                "- Each response must add NEW content\n"
                "</repetition_prevention>"
            )

        # Few-shot examples for tiny models
        if self.size_profile.include_few_shot:
            parts.append(self._build_few_shot_examples(context.mode))

        return "\n\n".join(parts) if parts else ""

    def _build_few_shot_examples(self, mode: str) -> str:
        """Build few-shot examples for very small models."""
        if mode == "continue":
            return """<examples>
<example type="good_continuation">
<last_assistant>The door creaked open, revealing a dimly lit chamber beyond.>
<continuation>Footsteps echoed on stone as you crossed the threshold. The air grew colder, carrying the scent of mildew and something metallic. In the corner, a shadow shifted—too deliberate to be natural.</continuation>
</example>
<example type="bad_continuation">
<last_assistant>The door creaked open, revealing a dimly lit chamber beyond.>
<continuation>The door creaked open slowly. You saw a chamber that was dimly lit. It was dark inside.</continuation>
</example>
</examples>"""
        return """<examples>
<example type="good_response">
<user>I examine the ancient sword on the wall.</user>
<assistant>The blade is rusted but the hilt remains ornate—gold inlay depicting a crown broken in three places. A name is etched near the base: "Vorthas the Usurper."</assistant>
</example>
<example type="bad_response">
<user>I examine the ancient sword on the wall.</user>
<assistant>You look at the sword. It is old and on the wall. The sword looks rusty.</assistant>
</example>
</examples>"""

    def _build_core_instructions(self, mode: str) -> str:
        """Build core story instructions."""
        if mode == "continue":
            return """<core_rules>
<rule>Continue directly from the endpoint of the last assistant message</rule>
<rule>Do not repeat, paraphrase, restart, or summarize prior text</rule>
<rule>Write only new narrative progression</rule>
<rule>Maintain consistent tone and style</rule>
</core_rules>"""
        return """<core_rules>
<rule>Preserve story state, character intent, and consequences</rule>
<rule>Advance the current scene without contradicting summary, lore, or recent turns</rule>
<rule>Keep tone consistent while avoiding repetitive phrasing</rule>
<rule>Introduce concrete developments: state changes, discoveries, conflicts, decisions</rule>
</core_rules>"""

    def _build_output_format_instructions(self, mode: str) -> str:
        """Build output format instructions with Thought/Speech/Action structure."""
        if mode == "continue":
            return """<output_format>
Your response can include three types of content, each serving a different purpose:

1. **Thoughts** `[...]` - Internal thinking, invisible to other characters
   - Use for: internal reasoning, private reactions, planning
   - Example: `[He's lying. I can tell by the way he won't meet my eyes.]`

2. **Speech** - Direct dialogue, visible to all characters
   - Use for: what the character says aloud
   - Example: `What do you mean you haven't seen him?`

3. **Actions** `(...)` - Physical behaviors, visible to all characters
   - Use for: gestures, movements, expressions
   - Example: `(She grips the hilt of her dagger, knuckles whitening.)`

Guidelines:
- Each type can appear 0 to multiple times per response as appropriate
- Keep thoughts concise but insightful - reveal subtext and internal conflict
- Actions should be concrete and specific, not generic
- Speech should reflect the character's voice and personality
- Balance all three for emotionally rich, nuanced responses
</output_format>"""
        return """<output_format>
Your response can include three types of content, each serving a different purpose:

1. **Thoughts** `[...]` - Internal thinking, invisible to the player
   - Use for: internal reasoning, private reactions, moral conflicts
   - Example: `[Another victim. When will this madness end?]`

2. **Speech** - Direct dialogue, audible to the player
   - Use for: what the character says aloud
   - Example: `You shouldn't have come here.`

3. **Actions** `(...)` - Physical behaviors, visible to the player
   - Use for: gestures, movements, expressions, atmosphere
   - Example: `(The torchlight flickers across his scarred face.)`

Guidelines:
- Each type can appear 0 to multiple times per response as appropriate
- Keep thoughts concise but insightful - reveal character depth and subtext
- Actions should create atmosphere and show, not tell
- Speech should be in character and advance the scene
- Balance all three for immersive, emotionally rich responses
</output_format>"""

    def build_messages(
        self,
        context: PromptContext,
    ) -> list[BaseMessage]:
        """Build Claude-formatted message list."""
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
            # Format user input with mode
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

    def inject_size_guidance(self, base_prompt: str, context: PromptContext) -> str:
        """Override to inject guidance in XML format."""
        # Guidance is already integrated in build_system_prompt
        return base_prompt
