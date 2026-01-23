from nicegui import ui

from src.frontend.ui_constants import TEXT_MUTED


def empty_state(text: str) -> None:
    ui.label(text).classes(TEXT_MUTED)
