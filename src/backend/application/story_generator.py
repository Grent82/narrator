from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from langchain_core.messages import HumanMessage, SystemMessage

from src.backend.api.schemas import StoryGenerateRequest
from src.backend.application.ports import ChatModelProtocol, LoggerProtocol
from src.backend.application.size_tier import SizeProfile, SizeTier, get_size_profile
from src.backend.application.story_generator_prompts import (
    GeneratorContext,
    get_generator_strategy,
)


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


def _build_prompts_with_strategy(
    model_name: str | None,
    size_profile: SizeProfile,
    ai_instruction_key: str,
    name: str,
    role: str,
    gender: str,
    age: str,
    traits: str,
    world_input: str,
    start_template: str,
    start_custom: str,
) -> tuple[str, str]:
    """Build provider-specific system and user prompts using strategy pattern.

    Args:
        model_name: The model identifier
        size_profile: Size profile for model-adapted guidance
        ai_instruction_key: The AI instruction key
        name, role, gender, age, traits: Character details
        world_input: World direction
        start_template, start_custom: Start template options

    Returns:
        Tuple of (system_prompt, user_prompt) formatted for the provider
    """
    strategy = get_generator_strategy(model_name=model_name, size_profile=size_profile)

    ctx = GeneratorContext(
        ai_instruction_key=ai_instruction_key,
        role=role,
        name=name,
        gender=gender,
        age=age,
        traits=traits,
        world_input=world_input,
        start_template=start_template,
        start_custom=start_custom,
        size_profile=size_profile,
    )

    return strategy.build_system_prompt(ctx), strategy.build_user_prompt(ctx)


def _request_more_lore(
    chat_model: ChatModelProtocol,
    logger: LoggerProtocol,
    deficits: dict,
    existing_titles: list[str],
    ai_instruction_key: str,
    world_input: str,
    size_tier: SizeTier,
) -> list[dict]:
    """Request additional lore entries based on size tier."""
    if size_tier in ("tiny", "small"):
        prompt = (
            "You are expanding a dark fantasy lore database.\n"
            "Return ONLY a JSON array. No markdown, no explanations.\n"
            "Each entry: {title, tag, description, triggers}\n"
            f"Allowed tags: {sorted(LORE_TAGS)}.\n"
            f"Existing titles to avoid: {existing_titles}\n"
            f"Need: {deficits}\n"
            f"World: {world_input}\n"
            "Descriptions: 60-180 words, vivid, concrete, unsettling.\n"
            "CRITICAL: Valid JSON only. No markdown fences.\n"
        )
    else:
        prompt = (
            f"Expand lore database. Return JSON array of entries.\n"
            f"Tags: {sorted(LORE_TAGS)}. Avoid: {existing_titles}\n"
            f"Need: {deficits}. World: {world_input}\n"
            "60-180 words per description. Vivid, concrete, avoid generic fantasy.\n"
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
    model_name: str | None = None,
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

    # Detect size tier for adaptive prompting
    size_profile = get_size_profile(model_name)
    size_tier = size_profile.tier
    logger.info("story_generator_size_tier=%s model=%s", size_tier, model_name or "unspecified")

    # Build provider-specific prompts using strategy pattern
    system_prompt, user_prompt = _build_prompts_with_strategy(
        model_name=model_name,
        size_profile=size_profile,
        ai_instruction_key=payload.ai_instruction_key,
        name=name,
        role=role,
        gender=gender,
        age=age,
        traits=traits,
        world_input=world_input,
        start_template=start_template,
        start_custom=start_custom,
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
            size_tier,
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
