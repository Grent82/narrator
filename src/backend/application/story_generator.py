from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from langchain_core.messages import HumanMessage, SystemMessage

from src.backend.api.schemas import StoryGenerateRequest
from src.backend.application.ports import ChatModelProtocol, LoggerProtocol


LORE_TAGS = {"Character", "Player", "Place", "Race", "Event", "Item", "Faction", "Rule", "Custom"}
MIN_TOTAL = 45
MAX_TOTAL = 55
MIN_PLACES = 5
MIN_CHARACTERS = 8
MIN_FACTIONS = 3


@dataclass(frozen=True)
class GeneratedStory:
    title: str
    description: str
    plot_essentials: str
    author_note: str
    tags: list[str]
    lore: list[dict]


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty generator response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _extract_json_with_repair(
    text: str,
    chat_model: ChatModelProtocol,
    logger: LoggerProtocol,
    repair_model: ChatModelProtocol | None = None,
) -> dict:
    try:
        return _extract_json(text)
    except Exception as exc:
        logger.warning("story_generator_json_parse_failed error=%s", exc)
    repair = repair_model or chat_model
    repair_prompt = (
        "You are a strict JSON repair tool.\n"
        "Fix the JSON so it is valid. Keep the same keys and structure.\n"
        "Do not add or remove entries except to fix broken JSON syntax.\n"
        "Return ONLY valid JSON. No explanations.\n"
    )
    response = repair.invoke([SystemMessage(content=repair_prompt), HumanMessage(content=text)])
    return _extract_json(getattr(response, "content", ""))


def _coerce_lore(entries: Iterable[dict]) -> list[dict]:
    normalized: list[dict] = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", "") or "").strip()
        tag = str(entry.get("tag", "") or "").strip()
        description = str(entry.get("description", "") or "").strip()
        triggers = str(entry.get("triggers", "") or "").strip()
        if not title or not tag:
            continue
        if tag not in LORE_TAGS:
            tag = "Custom"
        normalized.append(
            {
                "title": title,
                "tag": tag,
                "description": description,
                "triggers": triggers,
            }
        )
    return normalized


def _count_lore(entries: list[dict]) -> tuple[int, int, int]:
    total = len(entries)
    places = sum(1 for e in entries if e.get("tag") == "Place")
    chars = sum(1 for e in entries if e.get("tag") in {"Character", "Player"})
    factions = sum(1 for e in entries if e.get("tag") == "Faction")
    return total, places, chars, factions


def _ensure_player_entry(entries: list[dict], name: str, role: str, traits: str) -> None:
    name_lower = name.strip().lower()
    for entry in entries:
        if entry.get("tag") == "Player" and entry.get("title", "").strip().lower() == name_lower:
            return
    description = f"{name} is the player character. Role: {role}. {traits}".strip()
    entries.insert(
        0,
        {
            "title": name.strip() or "Player",
            "tag": "Player",
            "description": description,
            "triggers": name.strip(),
        },
    )


def _dedupe(entries: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for entry in entries:
        key = (entry.get("title", "").strip().lower(), entry.get("tag", ""))
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def _request_more_lore(
    chat_model: ChatModelProtocol,
    logger: LoggerProtocol,
    deficits: dict,
    existing_titles: list[str],
    ai_instruction_key: str,
    world_input: str,
) -> list[dict]:
    prompt = (
        "You are expanding a dark fantasy lore database in the vein of Joe Abercrombie, early GRRM, and FromSoftware.\n"
        "Return ONLY a JSON array of lore entries.\n"
        "Each entry must have: title, tag, description, triggers.\n"
        f"Allowed tags: {sorted(LORE_TAGS)}.\n"
        f"Do NOT use these existing titles: {existing_titles}\n"
        f"Target deficits: {deficits}\n"
        f"World hints: {world_input}\n"
        "Descriptions: 60–180 words, concrete, vivid, unsettling. Avoid generic fantasy.\n"
    )
    response = chat_model.invoke([SystemMessage(content=prompt), HumanMessage(content="Generate now.")])
    data = _extract_json(getattr(response, "content", ""))
    if isinstance(data, dict):
        data = data.get("lore", [])
    if not isinstance(data, list):
        return []
    return _coerce_lore(data)


def generate_story_blueprint(
    chat_model: ChatModelProtocol,
    payload: StoryGenerateRequest,
    logger: LoggerProtocol,
    repair_model: ChatModelProtocol | None = None,
) -> GeneratedStory:
    logger.info("story_generator_start preset=%s name=%s role=%s", payload.ai_instruction_key, payload.name, payload.role)
    role = payload.role.strip()
    name = payload.name.strip()
    gender = payload.gender.strip()
    age = payload.age.strip()
    traits = payload.traits.strip()
    world_input = payload.world_input.strip()
    start_template = payload.start_template.strip()
    start_custom = payload.start_custom.strip()

    start_combined = " ".join([part for part in [start_template, start_custom] if part])
    system_prompt = (
        "You are a masterful dark fantasy world-builder in the vein of Joe Abercrombie, early GRRM, "
        "and FromSoftware lore style. Your worlds feel ancient, cruel, morally gray, decaying, and "
        "steeped in tragic history.\n"
        "\n"
        "Core rules — you MUST obey these:\n"
        "• Return ONLY valid JSON. No explanation, no markdown, no ```json fence.\n"
        "• Keys: title, description, plot_essentials, author_note, tags (array), lore (array)\n"
        f"• lore = array of {MIN_TOTAL}–{MAX_TOTAL} objects, each with: \"title\", \"tag\", \"description\", \"triggers\"\n"
        f"• Allowed tags: {', '.join(sorted(LORE_TAGS))}\n"
        f"• Minimums: ≥{MIN_PLACES} distinct Places, ≥{MIN_CHARACTERS} named Characters/Player/NPCs with personality/motivation, "
        f"≥{MIN_FACTIONS} Factions with conflicting agendas\n"
        "• Every entry must feel alive: use concrete sensory details, hints of dark secrets, betrayals, ancient grudges, "
        "body horror, religious fanaticism, or ecological decay.\n"
        "• AVOID: generic fantasy (elves are graceful archers, dwarves love beer & axes, chosen-one farmboy, etc.)\n"
        "• MAKE IT DISTINCTIVE: twist classic tropes, add moral rot, body-horror undertones, unreliable narrators in descriptions.\n"
        "• Player entry comes first, tag='Player', title= exactly the provided name, triggers contains the name.\n"
        "• Descriptions: 60–180 words, vivid, immersive, slightly unsettling.\n"
        "• Triggers: comma-separated list of 1–6 exact-match phrases players might write.\n"
        "• Think step-by-step about the most interesting conflicts and secrets BEFORE writing JSON. "
        "Do NOT output your thinking.\n"
        "\n"
        "Format example (structure only, do not copy content):\n"
        "{\n"
        "  \"title\": \"...\",\n"
        "  \"description\": \"...\",\n"
        "  \"plot_essentials\": \"...\",\n"
        "  \"author_note\": \"...\",\n"
        "  \"tags\": [\"...\"],\n"
        "  \"lore\": [\n"
        "    {\"title\": \"...\", \"tag\": \"Place\", \"description\": \"...\", \"triggers\": \"...\"}\n"
        "  ]\n"
        "}\n"
    )
    user_prompt = (
        "Create a complete, self-contained dark fantasy world and story seed around this protagonist:\n\n"
        f"Name: {name}\n"
        f"Role/archetype: {role}\n"
        f"Gender: {gender or 'unspecified'}\n"
        f"Age: {age or 'unspecified'}\n"
        f"Core traits: {traits}\n\n"
        f"World direction / key inspirations: {world_input or 'classic grimdark fantasy with political intrigue and cosmic horror undertones'}\n\n"
        f"Opening situation: {start_combined or 'The character awakens in a dangerous situation with no clear memory of the previous days.'}\n\n"
        "Build a rich, dangerous, morally compromised world that feels worth exploring for many hours.\n"
    )
    logger.debug("story_generator_system_prompt=%s", system_prompt)
    logger.debug("story_generator_user_prompt=%s", user_prompt)
    response = chat_model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    data = _extract_json_with_repair(getattr(response, "content", ""), chat_model, logger, repair_model)

    title = str(data.get("title", "") or "").strip() or "Untitled Story"
    description = str(data.get("description", "") or "").strip()
    plot_essentials = str(data.get("plot_essentials", "") or "").strip()
    author_note = str(data.get("author_note", "") or "").strip()
    tags = [str(t).strip() for t in (data.get("tags") or []) if str(t).strip()]

    lore_entries = _coerce_lore(data.get("lore", []))
    traits_line = traits
    if gender:
        traits_line = f"{traits_line} Gender: {gender}."
    if age:
        traits_line = f"{traits_line} Age: {age}."
    _ensure_player_entry(lore_entries, name, role, traits_line)
    lore_entries = _dedupe(lore_entries)
    total, places, chars, factions = _count_lore(lore_entries)

    deficits = {
        "total_needed": max(0, MIN_TOTAL - total),
        "places_needed": max(0, MIN_PLACES - places),
        "characters_needed": max(0, MIN_CHARACTERS - chars),
        "factions_needed": max(0, MIN_FACTIONS - factions),
    }
    if any(value > 0 for value in deficits.values()):
        extra = _request_more_lore(
            chat_model,
            logger,
            deficits,
            [entry["title"] for entry in lore_entries],
            payload.ai_instruction_key,
            world_input,
        )
        lore_entries.extend(extra)
        lore_entries = _dedupe(lore_entries)

    if len(lore_entries) > MAX_TOTAL:
        lore_entries = lore_entries[:MAX_TOTAL]

    if not plot_essentials:
        essentials = f"{name} ({role}). {traits}".strip()
        if gender:
            essentials = f"{essentials} Gender: {gender}."
        if age:
            essentials = f"{essentials} Age: {age}."
        plot_essentials = essentials

    total, places, chars, factions = _count_lore(lore_entries)
    logger.info(
        "story_generator_done title=%s lore_total=%d places=%d characters=%d factions=%d",
        title,
        total,
        places,
        chars,
        factions,
    )
    return GeneratedStory(
        title=title,
        description=description,
        plot_essentials=plot_essentials,
        author_note=author_note,
        tags=tags,
        lore=lore_entries,
    )
