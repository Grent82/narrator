from typing import Iterable

from src.backend.infrastructure.models import LoreEntryModel, StoryModel


def _format_lore(entries: Iterable[LoreEntryModel]) -> str:
    lines = []
    for entry in entries:
        title = entry.title.strip() if entry.title else ""
        tag = entry.tag.strip() if entry.tag else ""
        triggers = entry.triggers.strip() if entry.triggers else ""
        description = entry.description.strip() if entry.description else ""
        header_parts = [part for part in [tag, title] if part]
        header = " - ".join(header_parts) if header_parts else "Lore Entry"
        lines.append(f"* {header}")
        if triggers:
            lines.append(f"  Triggers: {triggers}")
        if description:
            lines.append(f"  {description}")
    return "\n".join(lines)


def build_prompt(story: StoryModel, user_input: str) -> str:
    sections = []

    ai_instructions = (story.ai_instructions or "").strip()
    if ai_instructions:
        sections.append("[AI INSTRUCTIONS]\n" + ai_instructions)

    plot_summary = (story.plot_summary or "").strip()
    if plot_summary:
        sections.append("[PLOT SUMMARY]\n" + plot_summary)

    plot_essentials = (story.plot_essentials or "").strip()
    if plot_essentials:
        sections.append("[PLOT ESSENTIALS]\n" + plot_essentials)

    lore_block = _format_lore(story.lore_entries)
    if lore_block:
        sections.append("[LORE]\n" + lore_block)

    author_note = (story.author_note or "").strip()
    if author_note:
        sections.append("[AUTHOR NOTE]\n" + author_note)

    sections.append("[USER INPUT]\n" + user_input.strip())

    return "\n\n".join(sections)
