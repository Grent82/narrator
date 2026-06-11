from __future__ import annotations

from collections.abc import Iterable

from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.backend.application.input_formatting import format_input_block
from src.backend.application.ports import LoggerProtocol
from src.backend.application.prompt_renderer import render_profile_guidance, render_size_guidance
from src.backend.infrastructure.models import StoryModel


def _lore_value(entry, key: str, logger: LoggerProtocol = None) -> str:
    logger and logger.debug("lore_value entry=%s key=%s", entry, key)
    if isinstance(entry, Document):
        meta = entry.metadata or {}
        value = meta.get(key)
        if value is not None and str(value).strip():
            return str(value)
        if key in {"page_content", "description"}:
            content = getattr(entry, "page_content", "") or ""
            return str(content)
        return ""
    if hasattr(entry, key):
        return str(getattr(entry, key) or "")
    if isinstance(entry, dict):
        return str(entry.get(key, "") or "")
    return ""


def _should_skip_lore(entry, plot_essentials: str, logger: LoggerProtocol = None) -> bool:
    tag = _lore_value(entry, "tag", logger=logger).strip().lower()
    if tag in {"player", "player_character", "player character", "pc"}:
        return True
    essentials = (plot_essentials or "").strip().lower()
    if not essentials:
        return False
    title = _lore_value(entry, "title", logger=logger).strip().lower()
    if title and title in essentials:
        return True
    triggers = _lore_value(entry, "triggers", logger=logger).strip()
    if triggers:
        for raw in triggers.split(","):
            token = raw.strip().lower()
            if token and token in essentials:
                return True
    return False


def _format_lore(entries: Iterable, plot_essentials: str, logger: LoggerProtocol = None) -> str:
    lines = []
    for entry in entries:
        if _should_skip_lore(entry, plot_essentials, logger=logger):
            continue
        title = _lore_value(entry, "title", logger=logger).strip()
        tag = _lore_value(entry, "tag", logger=logger).strip()
        description = _lore_value(entry, "description", logger=logger).strip()
        if description:
            lines.append(f"* {tag} - {description}" if tag else f"* {description}")
        else:
            lines.append(f"* {title}" if title else "")
        logger and logger.debug(
            "lore_entry title=%s tag=%s description=%s",
            title,
            tag,
            description,
        )
    return "\n".join(lines)


def _message_value(msg, key: str, default=None):
    if hasattr(msg, key):
        return getattr(msg, key)
    if isinstance(msg, dict):
        return msg.get(key, default)
    return default


def build_system_prompt(
    story: StoryModel,
    lore_entries: Iterable | None = None,
    mode: str = "story",
    model_profile_id: str | None = None,
    model_name: str | None = None,
    logger: LoggerProtocol = None,
) -> str:
    """Build system prompt with optional model-adaptive enhancements.

    Args:
        story: The story model
        lore_entries: Optional lore entries to include
        mode: The operation mode (story, continue, say, do)
        model_profile_id: The model class profile ID
        model_name: The model identifier for size-tier detection
        logger: Optional logger

    Returns:
        The formatted system prompt
    """
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

    lore_block = _format_lore(
        lore_entries if lore_entries is not None else story.lore_entries,
        plot_essentials,
        logger=logger,
    ).strip()
    if lore_block:
        sections.append("[LORE]\n" + lore_block)

    author_note = (story.author_note or "").strip()
    if author_note:
        sections.append("[AUTHOR NOTE]\n" + author_note)

    # Model class profile guidance
    profile_guidance = render_profile_guidance(model_profile_id, mode, model_name).strip()
    if profile_guidance:
        sections.append("[MODEL-SPECIFIC GUIDANCE]\n" + profile_guidance)

    # Size-tier specific guidance (CoT, repetition prevention, etc.)
    size_guidance = render_size_guidance(model_name, mode).strip()
    if size_guidance:
        sections.append("[SIZE-ADAPTED GUIDANCE]\n" + size_guidance)

    return "\n\n".join(sections)


def _build_history_messages(
    messages: Iterable,
    max_pairs: int,
    overlap_pairs: int = 0,
) -> list[BaseMessage]:
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
    lore_entries: Iterable | None = None,
    recent_pairs: int = 3,
    overlap_pairs: int = 0,
    model_profile_id: str | None = None,
    model_name: str | None = None,
    logger: LoggerProtocol = None,
    use_strategy: bool = False,
) -> list[BaseMessage]:
    """Build chat messages with optional strategy-based prompting.

    Args:
        story: The story model
        user_text: The user's input text
        mode: The operation mode (story, continue, say, do)
        lore_entries: Optional lore entries to include
        recent_pairs: Number of recent message pairs to include
        overlap_pairs: Additional pairs for overlap context
        model_profile_id: The model class profile ID
        model_name: The model identifier for size-tier/strategy detection
        logger: Optional logger
        use_strategy: If True, use the new strategy-based approach (future)

    Returns:
        List of LangChain messages ready for the LLM
    """
    messages: list[BaseMessage] = []

    if story:
        system_prompt = build_system_prompt(
            story,
            lore_entries=lore_entries,
            mode=mode,
            model_profile_id=model_profile_id,
            model_name=model_name,
            logger=logger,
        )
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        if story.messages:
            messages.extend(_build_history_messages(story.messages, recent_pairs, overlap_pairs))

    messages.append(HumanMessage(content=format_input_block(mode, user_text)))
    return messages


# Strategy-based prompting (optional, opt-in)
def build_chat_messages_with_strategy(
    story: StoryModel | None,
    user_text: str,
    mode: str = "story",
    lore_entries: Iterable | None = None,
    recent_pairs: int = 3,
    overlap_pairs: int = 0,
    model_name: str | None = None,
    logger: LoggerProtocol = None,
) -> list[BaseMessage]:
    """Build chat messages using the new strategy-based approach.

    This function uses provider-specific strategies (Claude XML, Qwen Markdown, etc.)
    and size-adapted guidance for optimal prompt formatting.

    Args:
        story: The story model
        user_text: The user's input text
        mode: The operation mode (story, continue, say, do)
        lore_entries: Optional lore entries to include
        recent_pairs: Number of recent message pairs to include
        overlap_pairs: Additional pairs for overlap context
        model_name: The model identifier for strategy selection
        logger: Optional logger

    Returns:
        List of LangChain messages ready for the LLM
    """
    from src.backend.application.prompt_strategies.factory import get_prompt_strategy

    if not model_name:
        # Fall back to legacy approach
        return build_chat_messages(
            story=story,
            user_text=user_text,
            mode=mode,
            lore_entries=lore_entries,
            recent_pairs=recent_pairs,
            overlap_pairs=overlap_pairs,
            logger=logger,
        )

    strategy = get_prompt_strategy(model_name=model_name)

    # Build context for strategy
    from src.backend.application.prompt_strategies.base import PromptContext

    context = PromptContext(
        ai_instructions=story.ai_instructions if story else None,
        plot_summary=story.plot_summary if story else None,
        plot_essentials=story.plot_essentials if story else None,
        lore_block=_format_lore(
            lore_entries if lore_entries is not None else (story.lore_entries if story else []),
            story.plot_essentials if story else "",
            logger=logger,
        ).strip() if story else None,
        author_note=story.author_note if story else None,
        mode=mode,
        model_name=model_name,
        recent_messages=_build_history_messages(
            story.messages if story else [],
            recent_pairs,
            overlap_pairs,
        ),
        user_text=user_text,
    )

    return strategy.build_messages(context)
