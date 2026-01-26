import logging
from typing import Dict, List, Optional

import httpx

from src.frontend.config import BACKEND_URL
from src.frontend.story_defaults import DEFAULT_AI_INSTRUCTION_KEY, get_ai_instructions

Story = Dict[str, object]
Message = Dict[str, str]

_logger = logging.getLogger("frontend.state")
_client = httpx.Client(timeout=15.0)

_story_cache: Dict[str, Story] = {}
_story_order: List[str] = []


def _request(method: str, path: str, payload: dict | None = None) -> Optional[object]:
    url = f"{BACKEND_URL}{path}"
    try:
        response = _client.request(method, url, json=payload)
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()
    except Exception as exc:
        _logger.error("backend_request_failed method=%s path=%s error=%s", method, path, exc)
        return None


def list_story_ids() -> List[str]:
    data = _request("GET", "/stories")
    if not isinstance(data, list):
        return []
    _story_cache.clear()
    _story_order.clear()
    for item in data:
        story_id = str(item.get("id", ""))
        if not story_id:
            continue
        _story_cache[story_id] = item
        _story_order.append(story_id)
    return list(_story_order)


def _ensure_messages(story: Story) -> List[Message]:
    messages = story.get("messages")
    if not isinstance(messages, list):
        messages = []
        story["messages"] = messages
    return messages


def get_story(story_id: str) -> Optional[Story]:
    cached = _story_cache.get(story_id)
    if cached and "ai_instructions" in cached:
        _ensure_messages(cached)
        return cached
    data = _request("GET", f"/stories/{story_id}")
    if not isinstance(data, dict):
        return None
    _ensure_messages(data)
    _story_cache[story_id] = data
    return data


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
    payload = {
        "title": title,
        "ai_instruction_key": ai_instruction_key or DEFAULT_AI_INSTRUCTION_KEY,
        "ai_instructions": ai_instructions or get_ai_instructions(ai_instruction_key or DEFAULT_AI_INSTRUCTION_KEY),
        "plot_summary": "",
        "plot_essentials": plot_essentials,
        "author_note": author_note,
        "description": description,
        "tags": tags or [],
        "lore": lore_entries or [],
    }
    data = _request("POST", "/stories", payload)
    if not isinstance(data, dict):
        return ""
    story_id = str(data.get("id", ""))
    if story_id:
        _ensure_messages(data)
        _story_cache[story_id] = data
    return story_id


def delete_story(story_id: str) -> None:
    _request("DELETE", f"/stories/{story_id}")
    _story_cache.pop(story_id, None)
    if story_id in _story_order:
        _story_order.remove(story_id)


def append_message(story_id: str, role: str, text: str) -> None:
    story = _story_cache.get(story_id)
    if not story:
        return
    messages = _ensure_messages(story)
    messages.append({"role": role, "text": text})


def append_message_with_mode(story_id: str, role: str, text: str, mode: str | None = None) -> None:
    story = _story_cache.get(story_id)
    if not story:
        return
    messages = _ensure_messages(story)
    message = {"role": role, "text": text}
    if mode:
        message["mode"] = mode
    messages.append(message)


def update_last_message(story_id: str, text: str) -> None:
    story = _story_cache.get(story_id)
    if not story:
        return
    messages = _ensure_messages(story)
    if messages:
        messages[-1]["text"] = text


def get_story_messages(story_id: str) -> List[Message]:
    story = get_story(story_id)
    if not story:
        return []
    return _ensure_messages(story)


def recompute_summary(story_id: str, messages: List[Message]) -> None:
    payload = {"messages": messages}
    data = _request("POST", f"/stories/{story_id}/summary/recompute", payload)
    if isinstance(data, dict):
        story = _story_cache.get(story_id)
        if story is not None:
            story["plot_summary"] = data.get("plot_summary", "")


def update_story_field(story_id: str, field: str, value: str) -> None:
    payload = {field: value}
    data = _request("PUT", f"/stories/{story_id}", payload)
    if isinstance(data, dict):
        _story_cache[story_id] = data


def update_story_metadata(story_id: str, title: str, description: str, tags: List[str]) -> None:
    payload = {
        "title": title,
        "description": description,
        "tags": tags,
    }
    data = _request("PUT", f"/stories/{story_id}", payload)
    if isinstance(data, dict):
        _story_cache[story_id] = data


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
    payload = {
        "title": title,
        "ai_instruction_key": ai_instruction_key,
        "ai_instructions": ai_instructions,
        "plot_essentials": plot_essentials,
        "author_note": author_note,
        "description": description,
        "tags": tags,
        "lore": lore_entries,
    }
    data = _request("PUT", f"/stories/{story_id}", payload)
    if isinstance(data, dict):
        _story_cache[story_id] = data


def list_lore(story_id: str) -> List[Dict[str, str]]:
    data = _request("GET", f"/stories/{story_id}/lore")
    if isinstance(data, list):
        return data
    return []


def add_lore_entry(story_id: str, title: str, description: str, tag: str, triggers: str = "") -> str:
    payload = {
        "title": title,
        "description": description,
        "tag": tag,
        "triggers": triggers,
    }
    data = _request("POST", f"/stories/{story_id}/lore", payload)
    if isinstance(data, dict):
        return str(data.get("id", ""))
    return ""


def update_lore_entry(
    story_id: str,
    entry_id: str,
    title: str,
    description: str,
    tag: str,
    triggers: str = "",
) -> None:
    payload = {
        "id": entry_id,
        "title": title,
        "description": description,
        "tag": tag,
        "triggers": triggers,
    }
    _request("PUT", f"/stories/{story_id}/lore/{entry_id}", payload)


def delete_lore_entry(story_id: str, entry_id: str) -> None:
    _request("DELETE", f"/stories/{story_id}/lore/{entry_id}")
