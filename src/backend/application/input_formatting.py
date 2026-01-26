from __future__ import annotations


def normalize_mode(mode: str | None) -> str:
    value = (mode or "story").strip().lower()
    if value in {"do", "say", "story", "continue"}:
        return value
    return "story"


def format_input_block(mode: str | None, text: str | None) -> str:
    mode_value = normalize_mode(mode)
    text_value = (text or "").strip()
    return f"MODE: {mode_value.upper()}\nTEXT: {text_value}"


def format_user_for_summary(mode: str | None, text: str | None) -> str:
    mode_value = normalize_mode(mode)
    text_value = (text or "").strip()
    if mode_value == "continue":
        return ""
    if mode_value == "say":
        return f'You say: "{text_value}"' if text_value else ""
    if mode_value == "do":
        return f"You do: {text_value}" if text_value else ""
    return text_value
