import logging

from ollama import Client as OllamaClient

from src.backend.application.input_formatting import format_user_for_summary
from src.backend.infrastructure.models import StoryModel


SUMMARY_SYSTEM_PROMPT = """You are a concise story summarizer. 
- Update the existing summary with new information from the latest turn.
- Keep concise, factual, third-person perspective.
- Preserve all important names, locations, items, relationships, quests, consequences and key facts.
- Remove transient details (small talk, exact wording of dialogue unless plot-critical).
- Only add or revise information based on the new turn.
- Keep it concise and factual.
- Never invent or add facts that weren't explicitly stated.
- Return only the updated summary text.
"""

SUMMARY_FULL_SYSTEM_PROMPT = """You are a concise story summarizer.
- Create a summary of the story so far based on the full chat log.
- Keep concise, factual, third-person perspective.
- Preserve all important names, locations, items, relationships, quests, consequences and key facts.
- Remove transient details (small talk, exact wording of dialogue unless plot-critical).
- Never invent or add facts that weren't explicitly stated.
- Return only the summary text.
"""


def summarize_turn(
    client: OllamaClient,
    model: str,
    previous_summary: str,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: logging.Logger,
) -> str:
    previous = previous_summary.strip()
    prompt = (
        f"{SUMMARY_SYSTEM_PROMPT}\n"
        f"CURRENT SUMMARY:\n{previous}\n\n"
        f"NEW TURN:\n"
        f"User: {user_input.strip()}\n"
        f"Assistant: {assistant_text.strip()}\n\n"
        f"CONSTRAINT: Keep under {max_chars} characters.\n"
        f"UPDATED SUMMARY:\n"
    )
    try:
        response = client.generate(model=model, prompt=prompt)
        summary = (response.get("response", "") or "").strip()
        if not summary:
            return previous_summary
        if previous:
            min_len = max(200, int(len(previous) * 0.5))
            if len(summary) < min_len:
                return previous_summary
        if len(summary) > max_chars:
            summary = summary[:max_chars].rstrip()
        return summary
    except Exception:
        logger.exception("summary_update_failed")
        return previous_summary


def summarize_full(
    client: OllamaClient,
    model: str,
    messages: list[dict],
    max_chars: int,
    logger: logging.Logger,
) -> str:
    lines = []
    for msg in messages:
        role = str(msg.get("role", "")).strip().lower()
        text = (msg.get("text") or "").strip()
        if not text and role != "user":
            continue
        if role == "user":
            formatted = format_user_for_summary(msg.get("mode"), text)
            if not formatted:
                continue
            lines.append(f"User: {formatted}")
        elif role == "assistant" and text:
            lines.append(f"Assistant: {text}")
    if not lines:
        return ""
    prompt = (
        f"{SUMMARY_FULL_SYSTEM_PROMPT}\n"
        f"CHAT LOG:\n" + "\n".join(lines) + "\n\n"
        f"CONSTRAINT: Keep under {max_chars} characters.\n"
        f"SUMMARY:\n"
    )
    try:
        response = client.generate(model=model, prompt=prompt)
        summary = (response.get("response", "") or "").strip()
        if not summary:
            return ""
        if len(summary) > max_chars:
            summary = summary[:max_chars].rstrip()
        return summary
    except Exception:
        logger.exception("summary_recompute_failed")
        return ""


def update_story_summary(
    client: OllamaClient,
    model: str,
    story: StoryModel,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: logging.Logger,
) -> str:
    updated = summarize_turn(
        client=client,
        model=model,
        previous_summary=story.plot_summary or "",
        user_input=user_input,
        assistant_text=assistant_text,
        max_chars=max_chars,
        logger=logger,
    )
    story.plot_summary = updated
    return updated


def recompute_story_summary(
    client: OllamaClient,
    model: str,
    story: StoryModel,
    messages: list[dict],
    max_chars: int,
    logger: logging.Logger,
) -> str:
    updated = summarize_full(
        client=client,
        model=model,
        messages=messages,
        max_chars=max_chars,
        logger=logger,
    )
    story.plot_summary = updated
    story.ollama_context = []
    return updated
