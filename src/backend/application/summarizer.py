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
    """You are maintaining a factual story chronicle for a game system.

Your task:
- Rewrite the CURRENT SUMMARY into a plain, descriptive chronicle when needed, then update it with the latest turn.
- Keep concise, factual, chronological, third-person, past tense.
- Preserve important names, locations, items, relationships, quests, consequences, promises, threats, and state changes.
- Prefer clear statements of what happened over dramatic wording.
- Remove transient details: exact dialogue wording, sensual phrasing, atmospheric filler, repeated emotions, and decorative prose unless plot-critical.
- Do not mimic the narrator's style.
- Do not write like a novel, scene, or teaser text.
- Never invent or add facts that were not explicitly shown.
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
    """You are a precise, neutral chronicler maintaining campaign notes for a dark fantasy adventure.
Your task: rewrite the current chronicle into plain factual notes when needed, then update it ONLY with genuinely new, plot-relevant information from the latest player action and narrator response.

Core rules:
- Third-person perspective, past tense.
- Plain, descriptive, chronological prose. Think "campaign notes", not "novel excerpt".
- Preserve EVERY important proper name (characters, locations, items, factions, gods, curses...).
- Keep track of open quests, debts, alliances, betrayals, consequences, prophecies, ongoing threats.
- Only add / revise facts that are explicitly shown in the new turn — no assumptions, no inventions.
- Remove transient details: small talk, weather descriptions (unless plot-relevant), exact dialogue wording (unless it reveals key info or is a binding oath/promise), decorative sensual language, repeated emphasis, and scene-level prose.
- Do not mimic the narrator's voice, mood, or rhetoric.
- Do not end with dramatic closing lines.
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
