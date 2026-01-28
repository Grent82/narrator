from __future__ import annotations

from langchain_core.prompts import PromptTemplate

from src.backend.application.ports import ChatModelProtocol, LoggerProtocol
from src.backend.infrastructure.models import StoryModel


AI_INSTRUCTION_TO_SUMMARY_KEY = {
    "neutral_storyteller": "neutral_summarizer",
    "dark_storyteller": "dark_summarizer",
}


def resolve_summary_prompt_key(ai_instruction_key: str | None, fallback: str = "neutral") -> str:
    if not ai_instruction_key:
        return fallback
    return AI_INSTRUCTION_TO_SUMMARY_KEY.get(ai_instruction_key, fallback)
NEUTRAL_SUMMARY_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """You are a concise story summarizer.
- Update the existing summary with new important information from the latest turn only.
- Keep concise, factual, third-person perspective.
- Preserve all important names, locations, items, relationships, quests, consequences and key facts.
- Remove transient details (small talk, exact wording of dialogue unless plot-critical).
- Only add or revise information based on the new turn.
- Keep it concise and factual.
- Never invent or add facts that weren't explicitly stated.
- If nothing important changed, return the CURRENT SUMMARY unchanged.
- Return only the updated summary text.

CURRENT SUMMARY:
{summary}

LATEST TURN:
User: {user_input}
Assistant: {assistant_text}

UPDATED SUMMARY:
"""
)

DARK_SUMMARY_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """You are a precise, neutral chronicler of a dark fantasy adventure.
Your task: Update the existing story chronicle ONLY with genuinely new, plot-relevant information from the latest player action and narrator response.

Core rules:
- Third-person perspective, past tense.
- Preserve EVERY important proper name (characters, locations, items, factions, gods, curses...).
- Keep track of open quests, debts, alliances, betrayals, consequences, prophecies, ongoing threats.
- Only add / revise facts that are explicitly shown in the new turn — no assumptions, no inventions.
- Remove only truly transient details: small talk, weather descriptions (unless plot-relevant), exact dialogue wording (unless it reveals key info or is a binding oath/promise).
- If the new turn adds no meaningful plot progression (pure flavor / roleplay without consequences), return the CURRENT SUMMARY unchanged.
- Stay concise but never sacrifice clarity or key facts for brevity.
- Output format: ONLY the updated summary text — no explanations, no headers, no markdown.

CURRENT STORY CHRONICLE:
{summary}

LATEST TURN:
User (player): {user_input}
Narrator: {assistant_text}

UPDATED STORY CHRONICLE:
"""
)

SUMMARY_PROMPT_KEYS = {
    "neutral_summarizer": NEUTRAL_SUMMARY_PROMPT_TEMPLATE,
    "dark_summarizer": DARK_SUMMARY_PROMPT_TEMPLATE,
}


def summarize_turn(
    client: ChatModelProtocol,
    model: str,
    previous_summary: str,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: LoggerProtocol,
    summary_prompt_key: str = "neutral",
) -> str:
    previous = previous_summary.strip()
    try:
        llm = client
        current_model = getattr(client, "model", None)
        if current_model and current_model != model and hasattr(client, "model_copy"):
            llm = client.model_copy(update={"model": model})
        prompt_template = SUMMARY_PROMPT_KEYS.get(summary_prompt_key, NEUTRAL_SUMMARY_PROMPT_TEMPLATE)
        prompt = prompt_template.format(
            summary=previous,
            user_input=user_input.strip(),
            assistant_text=assistant_text.strip(),
        )
        if hasattr(llm, "invoke"):
            response = llm.invoke(prompt)
            summary = getattr(response, "content", response)
        else:
            response = llm(prompt)
            summary = getattr(response, "content", response)
        summary = (summary or "").strip()
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
    client: ChatModelProtocol,
    model: str,
    story: StoryModel,
    user_input: str,
    assistant_text: str,
    max_chars: int,
    logger: LoggerProtocol,
) -> str:
    summary_prompt_key = story.summary_prompt_key or resolve_summary_prompt_key(story.ai_instruction_key)
    updated = summarize_turn(
        client=client,
        model=model,
        previous_summary=story.plot_summary or "",
        user_input=user_input,
        assistant_text=assistant_text,
        max_chars=max_chars,
        logger=logger,
        summary_prompt_key=summary_prompt_key,
    )
    story.plot_summary = updated
    return updated
