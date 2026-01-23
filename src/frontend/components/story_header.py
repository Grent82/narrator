from typing import Callable

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, ROW_BETWEEN, TITLE


def story_header(title: str, on_back: Callable[[], None]) -> None:
    with ui.row().classes(f"{CONTENT_WIDTH} {ROW_BETWEEN}"):
        ui.button("Back to stories", on_click=on_back)
    ui.label(title).classes(TITLE)
