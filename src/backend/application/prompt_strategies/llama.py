"""Llama-specific prompt strategy using Markdown formatting.

Llama models (and similar instruct models like Dolphin) respond well to
clear Markdown structure with explicit instructions. This strategy implements:
- Markdown-based prompt structure
- Strong guidance for smaller models (7B-14B range)
- Clear section demarcation
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.backend.application.prompt_strategies.base import PromptContext, PromptStrategy
from src.backend.application.size_tier import SizeProfile, get_size_profile


class LlamaPromptStrategy(PromptStrategy):
    """Strategy for Llama/Dolphin and similar instruct models using Markdown."""

    def __init__(self, size_profile: SizeProfile | None = None):
        super().__init__(size_profile or get_size_profile(None))

    @property
    def provider_name(self) -> str:
        return "ollama"

    def build_system_prompt(self, context: PromptContext) -> str:
        """Build Llama-formatted system prompt with Markdown structure."""
        sections = []

        # System role
        role = self._build_role(context.mode)
        sections.append(role)

        # Context sections
        if context.ai_instructions:
            sections.append(f"## AI Instructions\n\n{context.ai_instructions}")

        if context.plot_summary:
            sections.append(f"## Current StoryState\n\n{context.plot_summary}")

        if context.plot_essentials:
            sections.append(f"## EssentialFacts\n\n{context.plot_essentials}")

        if context.lore_block:
            sections.append(f"## KnownLore\n\n{context.lore_block}")

        if context.author_note:
            sections.append(f"## AuthorNotes\n\n{context.author_note}")

        # Model-specific guidance (from existing profile system)
        if context.model_profile_id:
            from src.backend.application.prompt_renderer import (
                render_profile_guidance,
            )

            profile_guidance = render_profile_guidance(
                context.model_profile_id, context.mode
            )
            if profile_guidance:
                sections.append(f"## AdditionalGuidance\n\n{profile_guidance}")

        # Size-adapted guidance (critical for smaller models)
        size_guidance = self._build_size_guidance(context)
        if size_guidance:
            sections.append(size_guidance)

        # Task definition
        task = self._build_task(context.mode)
        sections.append(task)

        # Output format
        output = self._build_output_format(context.mode)
        sections.append(output)

        return "\n\n".join(sections)

    def _build_role(self, mode: str) -> str:
        """Build role definition."""
        if mode == "continue":
            return """# Role: Story Continuator

You continue narratives precisely from where they left off. Your specialty is seamless continuation without repetition."""
        return """# Role: Dark Fantasy Narrator

You are a grimdark fantasy storyteller in the style of Joe Abercrombie, early George R.R. Martin, and FromSoftware games.

Your narratives feature:
- Moral ambiguity and cruel fates
- Grounded, visceral descriptions
- Political intrigue and conflicting agendas
- Decay, betrayal, and consequences
- Concrete sensory details over abstract atmosphere"""

    def _build_size_guidance(self, context: PromptContext) -> str:
        """Build size-adapted guidance - critical for smaller models."""
        if not self.size_profile:
            return ""

        parts = []

        # Verbosity guidance
        if self.size_profile.verbosity == "compact":
            parts.append(
                "## ResponseLength\n\n"
                "Keep responses concise. Follow all instructions literally. Prioritize completeness over elaboration."
            )

        # CoT is ESSENTIAL for small models
        if self.size_profile.require_cot:
            if self.size_profile.cot_style == "explicit_tags":
                parts.append(
                    "## RequiredThinkingProcess\n\n"
                    "YOU MUST think before answering. Use the following structure:\n\n"
                    "```thinking\n"
                    "1. Analyze the current situation\n"
                    "2. Consider what logically comes next\n"
                    "3. Plan your response\n"
                    "```\n\n"
                    "After your thinking block, provide your actual response."
                )
            elif self.size_profile.cot_style == "implicit":
                if context.mode == "continue":
                    parts.append(
                        "## ThinkingSteps\n\n"
                        "Think through these questions BEFORE writing your response:\n\n"
                        "1. Where exactly did the last response end?\n"
                        "2. What is the immediate next sentence/beat?\n"
                        "3. How do I continue without repeating any words or phrases?\n\n"
                        "Write your analysis, then write the continuation."
                    )
                else:
                    parts.append(
                        "## ThinkingSteps\n\n"
                        "Think through these questions BEFORE writing your response:\n\n"
                        "1. What is the current situation?\n"
                        "2. What does the player's action cause?\n"
                        "3. What is the most interesting but logical consequence?\n\n"
                        "Write your analysis, then write the story response."
                    )

        # Repetition prevention is CRITICAL for small models
        if self.size_profile.repetition_risk in ("very_high", "high"):
            parts.append(
                "## CRITICAL-AvoidRepetition\n\n"
                "WARNING: Smaller models tend to repeat themselves. Follow these rules EXACTLY:\n\n"
                "- NEVER copy sentences from previous assistant messages\n"
                "- NEVER rephrase or paraphrase prior text\n"
                "- NEVER restart scenes or reset character states\n"
                "- NEVER use similar closing lines repeatedly\n"
                "- EVERY response must contain NEW content only\n"
                "- If you notice repetition, STOP and rewrite immediately\n\n"
                "Check your response against the last assistant message before finalizing."
            )
        elif self.size_profile.repetition_risk == "medium":
            parts.append(
                "## AvoidRepetition\n\n"
                "- Add new content rather than restating\n"
                "- Vary your phrasing and vocabulary\n"
                "- Check against prior responses for similarity"
            )

        # Few-shot examples very helpful for small models
        if self.size_profile.include_few_shot:
            parts.append(self._build_few_shot_examples(context.mode))

        return "\n\n".join(parts) if parts else ""

    def _build_few_shot_examples(self, mode: str) -> str:
        """Build few-shot examples - very important for small models."""
        if mode == "continue":
            return """## ExamplesOfGoodContinuation

### Example 1
**Last Response:** The door creaked open, revealing a dimly lit chamber beyond.
**Good Continuation:** Footsteps echoed on stone as you crossed the threshold. The air grew colder, carrying the scent of mildew and something metallic. In the corner, a shadow shifted—too deliberate to be natural.
**Why Good:** Continues directly, adds new sensory details, introduces new element

**Bad Continuation:** The door creaked open slowly. You saw a chamber that was dimly lit. It was dark inside.
**Why Bad:** Repeats the door opening, restates what was already said

### Example 2
**Last Response:** She drew her sword, the steel singing in the twilight.
**Good Continuation:** The first attacker lunged before the echo faded. Steel met steel with a shower of sparks, and she felt the impact vibrate up her arm.
**Why Good:** Continues the action, adds new development

**Bad Continuation:** She held her sword ready. The steel was sharp and dangerous. She was ready to fight.
**Why Bad:** Restates the sword drawing, adds no progression

---

KEY RULE: Continue from the END point. Do not repeat what came before."""
        return """## ExamplesOfGoodResponses

### Example 1
**User:** I examine the ancient sword on the wall.
**Good Response:** The blade is rusted but the hilt remains ornate—gold inlay depicting a crown broken in three places. A name is etched near the base: "Vorthas the Usurper."
**Why Good:** Specific details, new information, atmospheric

**Bad Response:** You look at the sword. It is old and on the wall. The sword looks rusty.
**Why Bad:** Generic, repetitive structure, adds little

### Example 2
**User:** What do you know about the Black Abbey?
**Good Response:** The abbey hasn't seen a living monk in three centuries. They say the bells still toll at vespers, though no hands pull the ropes. Pilgrims who venture inside don't return the same—if they return at all.
**Why Good:** Specific lore, atmospheric, invites further interaction

**Bad Response:** The abbey is old and dark. It is a scary place. People don't like it.
**Why Bad:** Generic, repetitive, adds no interesting detail

---

KEY RULE: Add NEW, SPECIFIC information. Be vivid but grounded."""

    def _build_task(self, mode: str) -> str:
        """Build task definition."""
        if mode == "continue":
            return """## Task: Continue the Story

You will continue the narrative from the exact endpoint of the last assistant message.

### Requirements
- Continue directly after the last words
- Do not repeat, paraphrase, restart, or summarize prior text
- Write only new narrative progression
- Maintain consistent tone and style
- Advance the scene with concrete developments"""
        return """## Task: Narrate the Story

You will respond to the player's action as an immersive dark fantasy narrator.

### Requirements
- Preserve story state, character intent, and consequences
- Advance the current scene without contradicting summary, lore, or recent turns
- Keep tone consistent while avoiding repetitive phrasing
- Introduce concrete developments: state changes, discoveries, conflicts, decisions
- Write in third person, past tense"""

    def _build_output_format(self, mode: str) -> str:
        """Build output format section."""
        return """## Output Format

- Write only the story response
- No meta-commentary or explanations
- No markdown formatting unless part of the narrative
- No section headers in your output
- Pure narrative prose only"""

    def build_messages(
        self,
        context: PromptContext,
    ) -> list[BaseMessage]:
        """Build Llama-formatted message list."""
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
