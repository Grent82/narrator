from typing import Callable, Optional

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, TITLE


def story_header(
    title: str,
    on_back: Callable[[], None],
    on_settings: Optional[Callable[[], None]] = None,
) -> None:
    with ui.column().classes(
        f"{CONTENT_WIDTH} sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800/60 py-2"
    ):
        with ui.row().classes(f"{CONTENT_WIDTH}"):
            ui.button("Back to stories", on_click=on_back)
        with ui.row().classes(f"{CONTENT_WIDTH} items-center justify-center gap-2"):
            ui.label(title).classes(f"{TITLE} text-center")
            if on_settings:
                ui.button(icon="settings", on_click=on_settings).props("flat")
