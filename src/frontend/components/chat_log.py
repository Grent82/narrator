from typing import Callable, Dict, Tuple

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, TEXT_MUTED, TEXT_PRE

Message = Dict[str, str]


def create_chat_log(messages: list[Message]) -> Tuple[ui.column, Callable[[str], None], Callable[[str], ui.label]]:
    log = ui.column().classes(f"{CONTENT_WIDTH} gap-2 max-w-3xl")
    for msg in messages:
        if msg.get("role") == "user":
            with log:
                ui.label(f"> {msg.get('text', '')}").classes(TEXT_MUTED)
        else:
            with log:
                ui.label(msg.get("text", "")).classes(TEXT_PRE)

    def append_user(text: str) -> None:
        with log:
            ui.label(f"> {text}").classes(TEXT_MUTED)

    def append_assistant(text: str = "") -> ui.label:
        with log:
            return ui.label(text).classes(TEXT_PRE)

    return log, append_user, append_assistant
