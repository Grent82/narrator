from typing import Iterable, Optional

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.backend.application.input_formatting import format_input_block
from src.backend.infrastructure.models import StoryModel


def _lore_value(entry, key: str) -> str:
    if isinstance(entry, Document):
        value = (entry.metadata or {}).get(key, "")
        return str(value) if value is not None else ""
    if hasattr(entry, key):
        return str(getattr(entry, key) or "")
    if isinstance(entry, dict):
        return str(entry.get(key, "") or "")
    return ""


def _format_lore(entries: Iterable) -> str:
    lines = []
    for entry in entries:
        title = _lore_value(entry, "title").strip()
        tag = _lore_value(entry, "tag").strip()
        description = _lore_value(entry, "description").strip()
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
    lore_entries: Optional[Iterable] = None,
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


def _build_history_messages(messages: Iterable, max_pairs: int, overlap_pairs: int = 0) -> list[BaseMessage]:
    history: list[BaseMessage] = []
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
        if role == "user":
            history.append(HumanMessage(content=content))
        else:
            history.append(AIMessage(content=content))
    if max_pairs <= 0:
        return []
    take_pairs = max_pairs + max(0, overlap_pairs)
    return history[-(take_pairs * 2) :]


def build_chat_messages(
    story: StoryModel | None,
    user_text: str,
    mode: str = "story",
    lore_entries: Optional[Iterable] = None,
    recent_pairs: int = 3,
    overlap_pairs: int = 0,
) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    if story:
        system_prompt = build_system_prompt(story, lore_entries=lore_entries)
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        if story.messages:
            messages.extend(_build_history_messages(story.messages, recent_pairs, overlap_pairs))
    messages.append(HumanMessage(content=format_input_block(mode, user_text)))
    return messages
