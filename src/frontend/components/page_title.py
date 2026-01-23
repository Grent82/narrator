from nicegui import ui

from src.frontend.ui_constants import TITLE


def page_title(text: str) -> None:
    ui.label(text).classes(TITLE)
