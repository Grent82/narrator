from typing import Dict, List, Optional

from src.frontend.story_defaults import DEFAULT_AI_INSTRUCTION_KEY, get_ai_instructions

Story = Dict[str, object]
Message = Dict[str, str]

_stories: Dict[str, Story] = {}
_story_order: List[str] = []
_story_counter = 1


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
