from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, List

from src.backend.application.ports import ChatModelProtocol
from src.backend.infrastructure.models import LoreEntryModel, LoreSuggestionModel

logger = logging.getLogger("backend")


PROMPT_TEMPLATE = """You are a lore extraction engine for a dark fantasy story.
Extract ONLY new or updated lore from the latest turn.

Rules:
- Output JSON array only. No markdown.
- Each item must include: type, title, description, triggers, confidence (0-1).
- type must be one of: Character, Location, Item, Faction, Creature, Event.
- If the latest turn adds no new lore, return [].
- Do not invent details. Use only facts from the latest turn.
- Avoid duplicates of existing lore titles.

Existing lore titles:
{existing_titles}

Latest turn:
User: {user_input}
Assistant: {assistant_text}
"""


@dataclass
class Suggestion:
    kind: str
    title: str
    tag: str
    description: str
    triggers: str
    confidence: float
    target_lore_id: str | None = None


def _normalize_title(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _parse_json_array(text: str) -> list:
    if not text:
        return []
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    payload = text[start : end + 1]
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _existing_title_map(entries: Iterable[LoreEntryModel]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for entry in entries:
        mapping[_normalize_title(entry.title)] = entry.id
    return mapping


def extract_suggestions(
    client: ChatModelProtocol,
    model: str,
    existing_entries: list[LoreEntryModel],
    user_input: str,
    assistant_text: str,
) -> list[Suggestion]:
    existing_titles = ", ".join(sorted(entry.title for entry in existing_entries))
    prompt = PROMPT_TEMPLATE.format(
        existing_titles=existing_titles or "None",
        user_input=user_input.strip(),
        assistant_text=assistant_text.strip(),
    )
    if hasattr(client, "invoke"):
        response = client.invoke(prompt)
        text = getattr(response, "content", response)
    else:
        response = client(prompt)
        text = getattr(response, "content", response)
    data = _parse_json_array(str(text))
    title_map = _existing_title_map(existing_entries)
    suggestions: list[Suggestion] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        tag = str(item.get("type", "Character")).strip() or "Character"
        description = str(item.get("description", "")).strip()
        triggers = str(item.get("triggers", "")).strip()
        confidence = float(item.get("confidence", 0))
        norm_title = _normalize_title(title)
        target_id = title_map.get(norm_title)
        kind = "UPDATE" if target_id else "NEW"
        suggestions.append(
            Suggestion(
                kind=kind,
                title=title,
                tag=tag,
                description=description,
                triggers=triggers,
                confidence=confidence,
                target_lore_id=target_id,
            )
        )
    return suggestions


def save_suggestions(
    story_id: str,
    user_input: str,
    assistant_text: str,
    existing_entries: list[LoreEntryModel],
    suggestions: list[Suggestion],
    db_session,
) -> int:
    title_map = _existing_title_map(existing_entries)
    created = 0
    for suggestion in suggestions:
        if suggestion.confidence < 0.6:
            continue
        normalized = _normalize_title(suggestion.title)
        target_id = suggestion.target_lore_id or title_map.get(normalized)
        exists = (
            db_session.query(LoreSuggestionModel)
            .filter(
                LoreSuggestionModel.story_id == story_id,
                LoreSuggestionModel.title == suggestion.title,
                LoreSuggestionModel.kind == suggestion.kind,
                LoreSuggestionModel.status == "pending",
            )
            .first()
        )
        if exists:
            continue
        db_session.add(
            LoreSuggestionModel(
                story_id=story_id,
                kind=suggestion.kind,
                status="pending",
                title=suggestion.title,
                tag=suggestion.tag,
                description=suggestion.description,
                triggers=suggestion.triggers,
                target_lore_id=target_id,
                source_user=user_input,
                source_assistant=assistant_text,
            )
        )
        created += 1
    db_session.commit()
    return created
