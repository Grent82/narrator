from typing import Callable, Dict, Tuple

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, TEXT_MUTED, TEXT_PRE

Message = Dict[str, str]


def format_user_message(text: str, mode: str | None = None) -> str:
    mode_value = (mode or "story").strip().lower()
    if mode_value == "say":
        return f'You say: "{text}"' if text else ""
    if mode_value == "do":
        return f"You do: {text}" if text else ""
    if mode_value == "continue":
        return ""
    return text


def create_chat_log(
    messages: list[Message],
) -> Tuple[ui.column, Callable[[str, str | None], None], Callable[[str], ui.label], Callable[[list[Message]], None]]:
    log = ui.column().classes(f"{CONTENT_WIDTH} gap-2 max-w-3xl")

    def render(existing: list[Message]) -> None:
        log.clear()
        for msg in existing:
            if msg.get("role") == "user":
                formatted = format_user_message(str(msg.get("text", "")), msg.get("mode"))
                if not formatted:
                    continue
                with log:
                    ui.label(f"> {formatted}").classes(TEXT_MUTED)
            else:
                with log:
                    ui.label(msg.get("text", "")).classes(TEXT_PRE)

    def append_user(text: str, mode: str | None = None) -> None:
        formatted = format_user_message(text, mode)
        if not formatted:
            return
        with log:
            ui.label(f"> {formatted}").classes(TEXT_MUTED)

    def append_assistant(text: str = "") -> ui.label:
        with log:
            return ui.label(text).classes(TEXT_PRE)

    render(messages)
    return log, append_user, append_assistant, render
