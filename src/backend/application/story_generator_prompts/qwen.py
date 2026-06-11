"""Qwen-specific story generator strategy using Markdown formatting.

Qwen models respond well to Markdown-structured prompts similar to GPT models.
This strategy implements Markdown-based formatting for world-generation prompts.
"""

from __future__ import annotations

from src.backend.application.story_generator_prompts.base import (
    GeneratorContext,
    StoryGeneratorStrategy,
)


class QwenGeneratorStrategy(StoryGeneratorStrategy):
    """Strategy for Qwen models using Markdown formatting."""

    @property
    def provider_name(self) -> str:
        return "qwen"

    def build_system_prompt(self, ctx: GeneratorContext) -> str:
        """Build Qwen-formatted system prompt with Markdown structure."""
        size_tier = self.size_profile.tier

        # Size-adapted configuration
        if size_tier in ("tiny", "small"):
            cot_instruction = (
                "## Thinking Process\n\n"
                "Before writing JSON, analyze step-by-step:\n\n"
                "1. Geography and threats\n"
                "2. Factions and conflicts\n"
                "3. Characters and motivations\n"
                "4. History and secrets\n\n"
                "Write your reasoning first, then output the JSON."
            )
            guidance_density = (
                "## Critical Rules\n\n"
                "- JSON MUST be valid - no markdown, no explanations\n"
                "- Each description: 60-180 words, concrete details\n"
                "- NO generic fantasy tropes\n"
                "- Consistent character spellings throughout\n"
                "- Each entry must feel alive with dark secrets, betrayals, moral decay"
            )
            json_example = (
                "## Example Output\n\n"
                "```json\n"
                "{\n"
                '  "title": "Kingdom of Valdor",\n'
                '  "description": "A proud nation at the edge of the Northern Mountains...",\n'
                '  "plot_essentials": "Valdor defends humanity from orcs...",\n'
                '  "author_note": "Tone: grim, industrial, morally gray",\n'
                '  "tags": ["Place", "Faction", "Character"],\n'
                '  "lore": [\n'
                '    {"title": "Kingdom of Valdor", "tag": "Place", "description": "60-180 words...", "triggers": "Valdor, northern frontier"},\n'
                '    {"title": "Prince Gero", "tag": "Character", "description": "60-180 words...", "triggers": "Gero, ruler"}\n'
                "  ]\n"
                "}\n"
                "```\n"
            )
        elif size_tier == "medium":
            cot_instruction = (
                "## Thinking Process\n\n"
                "Plan your world systematically before writing JSON:\n"
                "- Geography and threats\n"
                "- Factions and conflicts\n"
                "- Characters and motivations\n"
                "- History and secrets\n\n"
                "Write your analysis, then write the JSON."
            )
            guidance_density = (
                "## Rules\n\n"
                "- Return valid JSON only\n"
                "- Descriptions: 60-180 words, vivid and concrete\n"
                "- Avoid generic fantasy\n"
                "- Keep character names consistent"
            )
            json_example = (
                "## Example Structure\n\n"
                "```json\n"
                '{ "title": "...", "description": "...", "plot_essentials": "...", '
                '"author_note": "...", "tags": ["..."], "lore": [...] }\n'
                "```\n"
            )
        else:
            cot_instruction = (
                "## Thinking Process\n\n"
                "Consider world-building systematically, then output JSON."
            )
            guidance_density = (
                "## Rules\n\n"
                "- Return valid JSON\n"
                "- Descriptions: 60-180 words\n"
                "- Avoid generic fantasy tropes"
            )
            json_example = (
                "## Structure\n\n"
                "{title, description, plot_essentials, author_note, tags[], lore[]}\n"
            )

        return (
                "# Role: Dark Fantasy World-Builder\n\n"
                "You are a masterful dark fantasy world-builder in the vein of Joe Abercrombie, "
                "early GRRM, and FromSoftware.\n\n"
                "Your worlds feel ancient, cruel, morally gray, decaying, and steeped in tragic history.\n\n"
                f"{cot_instruction}\n\n"
                f"{guidance_density}\n\n"
                "## Core Structure\n\n"
                "- Return ONLY valid JSON. No markdown fences, no explanations.\n"
                "- Keys: title, description, plot_essentials, author_note, tags (array), lore (array)\n"
                "- lore = array of 45–55 entries with: title, tag, description, triggers\n"
                "- Allowed tags: Character, Player, Place, Race, Event, Item, Faction, Rule, Custom\n"
                "- Minimums: ≥5 Places, ≥8 Characters, ≥3 Factions\n\n"
                f"{json_example}\n"
                "## Character Name Consistency\n\n"
                "Use ONE spelling per character. 'Valerian' not 'Valerius'. "
                "Title variations OK ('Valerian', 'Prince Valerian'), but core spelling must match."
            )

    def build_user_prompt(self, ctx: GeneratorContext) -> str:
        """Build Qwen-formatted user prompt with Markdown structure."""
        start_combined = " ".join([part for part in [ctx.start_template, ctx.start_custom] if part])

        return (
            "# Create a Dark Fantasy World and Story Seed\n\n"
            "## Protagonist\n\n"
            f"- **Name:** {ctx.name}\n"
            f"- **Role:** {ctx.role}\n"
            f"- **Gender:** {ctx.gender or 'unspecified'}\n"
            f"- **Age:** {ctx.age or 'unspecified'}\n"
            f"- **Traits:** {ctx.traits}\n\n"
            "## World Direction\n\n"
            f"{ctx.world_input or 'grimdark fantasy with political intrigue and cosmic horror'}\n\n"
            "## Opening\n\n"
            f"{start_combined or 'Character awakens in danger with no memory'}\n\n"
            "## Task\n\n"
            "Build a rich, dangerous, morally compromised world worth exploring for hours.\n\n"
            "**Output ONLY valid JSON. No markdown fences, no explanations.**"
        )
