from typing import Iterable, Optional

from src.backend.infrastructure.models import LoreEntryModel, StoryModel


def _format_lore(entries: Iterable[LoreEntryModel]) -> str:
    lines = []
    for entry in entries:
        title = entry.title.strip() if entry.title else ""
        tag = entry.tag.strip() if entry.tag else ""
        description = entry.description.strip() if entry.description else ""
        lines.append(f"* {tag} - {description}" if description else f"* {tag} - {title}")
    return "\n".join(lines)


def build_prompt(
    story: StoryModel,
    user_input: str,
    lore_entries: Optional[Iterable[LoreEntryModel]] = None,
) -> str:
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

    lore_block = _format_lore(lore_entries if lore_entries is not None else story.lore_entries)
    if lore_block:
        sections.append("[LORE]\n" + lore_block)

    author_note = (story.author_note or "").strip()
    if author_note:
        sections.append("[AUTHOR NOTE]\n" + author_note)

    sections.append("[USER INPUT]\n" + user_input.strip())

    return "\n\n".join(sections)
