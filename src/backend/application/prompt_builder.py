from typing import Iterable, Optional

from src.backend.application.input_formatting import format_input_block
from src.backend.infrastructure.models import LoreEntryModel, StoryModel


def _format_lore(entries: Iterable[LoreEntryModel]) -> str:
    lines = []
    for entry in entries:
        title = entry.title.strip() if entry.title else ""
        tag = entry.tag.strip() if entry.tag else ""
        description = entry.description.strip() if entry.description else ""
        lines.append(f"* {tag} - {description}" if description else f"* {tag} - {title}")
    return "\n".join(lines)


def _message_value(msg, key: str, default=None):
    if hasattr(msg, key):
        return getattr(msg, key)
    if isinstance(msg, dict):
        return msg.get(key, default)
    return default


def build_system_prompt(
    story: StoryModel,
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

    return "\n\n".join(sections)


def _build_history_messages(messages: Iterable, max_pairs: int) -> list[dict]:
    history = []
    for msg in messages:
        role = str(_message_value(msg, "role", "")).strip().lower()
        if role not in {"user", "assistant"}:
            continue
        text = str(_message_value(msg, "text", "") or "")
        if role == "assistant" and not text.strip():
            continue
        if role == "user":
            mode = _message_value(msg, "mode", None)
            content = format_input_block(mode, text)
        else:
            content = text
        history.append({"role": role, "content": content})
    if max_pairs <= 0:
        return []
    return history[-(max_pairs * 2) :]


def build_chat_messages(
    story: StoryModel | None,
    user_text: str,
    mode: str = "story",
    lore_entries: Optional[Iterable[LoreEntryModel]] = None,
    recent_pairs: int = 3,
) -> list[dict]:
    messages = []
    if story:
        system_prompt = build_system_prompt(story, lore_entries=lore_entries)
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if story.messages:
            messages.extend(_build_history_messages(story.messages, recent_pairs))
    messages.append({"role": "user", "content": format_input_block(mode, user_text)})
    return messages
