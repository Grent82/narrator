from src.backend.application.ports import LoggerProtocol, OllamaProtocol

from src.backend.infrastructure.models import StoryModel


SUMMARY_SYSTEM_PROMPT = """You are a concise story summarizer.
- Update the existing summary with new important information from the latest turn only.
- Keep concise, factual, third-person perspective.
- Preserve all important names, locations, items, relationships, quests, consequences and key facts.
- Remove transient details (small talk, exact wording of dialogue unless plot-critical).
- Only add or revise information based on the new turn.
- Keep it concise and factual.
- Never invent or add facts that weren't explicitly stated.
- If nothing important changed, return the CURRENT SUMMARY unchanged.
- Return only the updated summary text.
"""


def summarize_turn(
    client: OllamaProtocol,
    model: str,
    previous_summary: str,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: LoggerProtocol,
) -> str:
    previous = previous_summary.strip()
    prompt = (
        f"{SUMMARY_SYSTEM_PROMPT}\n"
        f"CURRENT SUMMARY:\n{previous}\n\n"
        f"NEW TURN:\n"
        f"User: {user_input.strip()}\n"
        f"Assistant: {assistant_text.strip()}\n\n"
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


def update_story_summary(
    client: OllamaProtocol,
    model: str,
    story: StoryModel,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: LoggerProtocol,
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
