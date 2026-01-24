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


def create_story(title: str, ai_instruction_key: str | None = None) -> str:
    global _story_counter
    story_id = f"story-{_story_counter}"
    _story_counter += 1
    instruction_key = ai_instruction_key or DEFAULT_AI_INSTRUCTION_KEY
    story: Story = {
        "id": story_id,
        "title": title.strip() or "Untitled Story",
        "messages": [],
        "ai_instructions": get_ai_instructions(instruction_key),
        "plot_summary": "",
        "plot_essentials": "",
        "author_note": "",
        "lore": [],
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
