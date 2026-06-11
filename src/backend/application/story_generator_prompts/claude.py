"""Claude-specific story generator strategy using XML formatting.

Anthropic recommends XML tags for structuring prompts to Claude models.
This strategy implements XML-based formatting for world-generation prompts.
"""

from __future__ import annotations

from src.backend.application.story_generator_prompts.base import (
    GeneratorContext,
    StoryGeneratorStrategy,
)


class ClaudeGeneratorStrategy(StoryGeneratorStrategy):
    """Strategy for Claude/Anthropic models using XML formatting."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def build_system_prompt(self, ctx: GeneratorContext) -> str:
        """Build Claude-formatted system prompt with XML structure."""
        size_tier = self.size_profile.tier

        # Size-adapted configuration
        if size_tier in ("tiny", "small"):
            cot_instruction = (
                "Think through the world step-by-step before writing JSON:\n"
                "1. Geography and threats\n"
                "2. Factions and conflicts\n"
                "3. Characters and motivations\n"
                "4. History and secrets\n\n"
                "Write your thinking in <thinking> tags, then output the JSON."
            )
            guidance_density = (
                "<critical_rules>\n"
                "• JSON MUST be valid - no markdown, no explanations\n"
                "• Each description: 60-180 words, concrete details\n"
                "• NO generic fantasy tropes\n"
                "• Consistent character spellings throughout\n"
                "• Each entry must feel alive with dark secrets, betrayals, moral decay\n"
                "</critical_rules>"
            )
            json_example = (
                "<example_output>\n"
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
                "</example_output>"
            )
        elif size_tier == "medium":
            cot_instruction = (
                "Plan your world systematically before writing JSON. "
                "Consider conflicts, factions, and character motivations."
            )
            guidance_density = (
                "<rules>\n"
                "• Return valid JSON only\n"
                "• Descriptions: 60-180 words, vivid and concrete\n"
                "• Avoid generic fantasy\n"
                "• Keep character names consistent\n"
                "</rules>"
            )
            json_example = (
                "<example_structure>\n"
                '{ "title": "...", "description": "...", "plot_essentials": "...", '
                '"author_note": "...", "tags": ["..."], "lore": [...] }\n'
                "</example_structure>"
            )
        else:
            cot_instruction = (
                "Consider world-building systematically, then output JSON."
            )
            guidance_density = (
                "Return valid JSON. Descriptions: 60-180 words. Avoid generic fantasy tropes."
            )
            json_example = (
                "<structure>\n"
                "{title, description, plot_essentials, author_note, tags[], lore[]}\n"
                "</structure>"
            )

        # Build XML-structured system prompt
        return (
            "<system>\n"
            "You are a masterful dark fantasy world-builder in the vein of Joe Abercrombie, "
            "early GRRM, and FromSoftware.\n"
            "Your worlds feel ancient, cruel, morally gray, decaying, and steeped in tragic history.\n"
            "</system>\n\n"
            f"<thinking_guidance>\n{cot_instruction}\n</thinking_guidance>\n\n"
            f"{guidance_density}\n\n"
            "<core_structure>\n"
            "• Return ONLY valid JSON. No markdown, no explanations, no ```json fences.\n"
            "• Keys: title, description, plot_essentials, author_note, tags (array), lore (array)\n"
            "• lore = array of 45–55 entries with: title, tag, description, triggers\n"
            "• Allowed tags: Character, Player, Place, Race, Event, Item, Faction, Rule, Custom\n"
            "• Minimums: ≥5 Places, ≥8 Characters, ≥3 Factions\n"
            "</core_structure>\n\n"
            "<triggers_definition>\n"
            "The 'triggers' field must contain SHORT KEYWORDS or SHORT PHRASES (not full sentences),\n"
            "separated by commas. These are the words/phrases that would trigger this lore entry\n"
            "to appear in the story context.\n\n"
            "GOOD examples: 'Valdor, northern frontier, kingdom'\n"
            "GOOD examples: 'Gero, prince, ruler, succession'\n"
            "GOOD examples: 'User, player character, amnesia, awakening'\n"
            "BAD example: 'Annabeth mentions waiting for Kael' (this is a sentence, not a trigger)\n"
            "BAD example: 'User pushes off table and strides through press of bodies' (too long)\n\n"
            "Format: keyword1, keyword2, keyword3\n"
            "</triggers_definition>\n\n"
            f"{json_example}\n\n"
            "<character_name_consistency>\n"
            "Use ONE spelling per character. 'Valerian' not 'Valerius'. "
            "Title variations OK ('Valerian', 'Prince Valerian'), but core spelling must match.\n"
            "</character_name_consistency>"
        )

    def build_user_prompt(self, ctx: GeneratorContext) -> str:
        """Build Claude-formatted user prompt with XML structure."""
        start_combined = " ".join([part for part in [ctx.start_template, ctx.start_custom] if part])

        return (
            "<user_input>\n"
            "Create a dark fantasy world and story seed around this protagonist:\n"
            "</user_input>\n\n"
            f"<protagonist>\n"
            f"<name>{ctx.name}</name>\n"
            f"<role>{ctx.role}</role>\n"
            f"<gender>{ctx.gender or 'unspecified'}</gender>\n"
            f"<age>{ctx.age or 'unspecified'}</age>\n"
            f"<traits>{ctx.traits}</traits>\n"
            f"</protagonist>\n\n"
            f"<world_direction>\n"
            f"{ctx.world_input or 'grimdark fantasy with political intrigue and cosmic horror'}\n"
            f"</world_direction>\n\n"
            f"<opening>\n"
            f"{start_combined or 'Character awakens in danger with no memory'}\n"
            f"</opening>\n\n"
            "<instruction>\n"
            "Build a rich, dangerous, morally compromised world worth exploring for hours.\n"
            "Output ONLY valid JSON.\n"
            "</instruction>"
        )
