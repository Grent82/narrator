from typing import Dict, List, Optional

Story = Dict[str, object]
Message = Dict[str, str]

_stories: Dict[str, Story] = {}
_story_order: List[str] = []
_story_counter = 1


def list_story_ids() -> List[str]:
    return list(_story_order)


def get_story(story_id: str) -> Optional[Story]:
    return _stories.get(story_id)


def create_story(title: str) -> str:
    global _story_counter
    story_id = f"story-{_story_counter}"
    _story_counter += 1
    story: Story = {
        "id": story_id,
        "title": title.strip() or "Untitled Story",
        "messages": [],
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
