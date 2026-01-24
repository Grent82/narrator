from typing import Callable, Optional

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, ROW_BETWEEN, TITLE


def story_header(
    title: str,
    on_back: Callable[[], None],
    on_settings: Optional[Callable[[], None]] = None,
) -> None:
    with ui.row().classes(f"{CONTENT_WIDTH} {ROW_BETWEEN}"):
        ui.button("Back to stories", on_click=on_back)
        if on_settings:
            ui.button(icon="settings", on_click=on_settings).props("flat")
    ui.label(title).classes(TITLE)
