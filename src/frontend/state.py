from typing import Dict, List, Optional

from src.frontend.story_defaults import DEFAULT_AI_INSTRUCTION_KEY, get_ai_instructions

Story = Dict[str, object]
Message = Dict[str, str]

_stories: Dict[str, Story] = {}
_story_order: List[str] = []
_story_counter = 1
_lore_counter = 1


def list_story_ids() -> List[str]:
    return list(_story_order)


def get_story(story_id: str) -> Optional[Story]:
    return _stories.get(story_id)


def _ensure_lore_counter(entry_id: str) -> None:
    global _lore_counter
    if entry_id.startswith("lore-"):
        suffix = entry_id[5:]
        if suffix.isdigit():
            num = int(suffix)
            if num >= _lore_counter:
                _lore_counter = num + 1


def _normalize_lore_entries(lore_entries: List[Dict[str, str]] | None) -> List[Dict[str, str]]:
    global _lore_counter
    normalized: List[Dict[str, str]] = []
    for entry in lore_entries or []:
        entry_id = str(entry.get("id", "")).strip()
        if entry_id:
            _ensure_lore_counter(entry_id)
        else:
            entry_id = f"lore-{_lore_counter}"
            _lore_counter += 1
        normalized.append(
            {
                "id": entry_id,
                "title": str(entry.get("title", "")).strip(),
                "description": str(entry.get("description", "")).strip(),
                "tag": str(entry.get("tag", "")).strip().upper(),
                "triggers": str(entry.get("triggers", "")).strip(),
            }
        )
    return normalized


def create_story(
    title: str,
    ai_instruction_key: str | None = None,
    ai_instructions: str | None = None,
    plot_essentials: str = "",
    author_note: str = "",
    description: str = "",
    tags: List[str] | None = None,
    lore_entries: List[Dict[str, str]] | None = None,
) -> str:
    global _story_counter
    story_id = f"story-{_story_counter}"
    _story_counter += 1
    instruction_key = ai_instruction_key or DEFAULT_AI_INSTRUCTION_KEY
    final_instructions = ai_instructions if ai_instructions is not None else get_ai_instructions(instruction_key)
    story: Story = {
        "id": story_id,
        "title": title.strip() or "Untitled Story",
        "messages": [],
        "ai_instruction_key": instruction_key,
        "ai_instructions": final_instructions,
        "plot_summary": "",
        "plot_essentials": plot_essentials.strip(),
        "author_note": author_note.strip(),
        "description": description.strip(),
        "tags": tags or [],
        "lore": _normalize_lore_entries(lore_entries),
    }
    _stories[story_id] = story
    _story_order.insert(0, story_id)
    return story_id


def delete_story(story_id: str) -> None:
    _stories.pop(story_id, None)
    if story_id in _story_order:
        _story_order.remove(story_id)


def append_message(story_id: str, role: str, text: str) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    messages = story.setdefault("messages", [])
    messages.append({"role": role, "text": text})


def update_story_field(story_id: str, field: str, value: str) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    story[field] = value


def update_story_metadata(story_id: str, title: str, description: str, tags: List[str]) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    story["title"] = title.strip() or "Untitled Story"
    story["description"] = description.strip()
    story["tags"] = tags


def update_story_from_editor(
    story_id: str,
    title: str,
    ai_instruction_key: str,
    ai_instructions: str,
    plot_essentials: str,
    author_note: str,
    description: str,
    tags: List[str],
    lore_entries: List[Dict[str, str]],
) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    story["title"] = title.strip() or "Untitled Story"
    story["ai_instruction_key"] = ai_instruction_key
    story["ai_instructions"] = ai_instructions
    story["plot_essentials"] = plot_essentials.strip()
    story["author_note"] = author_note.strip()
    story["description"] = description.strip()
    story["tags"] = tags
    story["lore"] = _normalize_lore_entries(lore_entries)


def list_lore(story_id: str) -> List[Dict[str, str]]:
    story = _stories.get(story_id)
    if not story:
        return []
    return list(story.get("lore", []))


def add_lore_entry(story_id: str, title: str, description: str, tag: str, triggers: str = "") -> str:
    global _lore_counter
    story = _stories.get(story_id)
    if not story:
        return ""
    entry_id = f"lore-{_lore_counter}"
    _lore_counter += 1
    entry = {
        "id": entry_id,
        "title": title.strip(),
        "description": description.strip(),
        "tag": tag.strip().upper(),
        "triggers": triggers.strip(),
    }
    lore = story.setdefault("lore", [])
    lore.insert(0, entry)
    return entry_id


def update_lore_entry(
    story_id: str,
    entry_id: str,
    title: str,
    description: str,
    tag: str,
    triggers: str = "",
) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    for entry in story.get("lore", []):
        if entry.get("id") == entry_id:
            entry["title"] = title.strip()
            entry["description"] = description.strip()
            entry["tag"] = tag.strip().upper()
            entry["triggers"] = triggers.strip()
            return


def delete_lore_entry(story_id: str, entry_id: str) -> None:
    story = _stories.get(story_id)
    if not story:
        return
    lore = story.get("lore", [])
    story["lore"] = [entry for entry in lore if entry.get("id") != entry_id]
