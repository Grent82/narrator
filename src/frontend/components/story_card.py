from typing import Callable

from nicegui import ui

from src.frontend.components.dialogs import confirm_delete_dialog
from src.frontend.ui_constants import CONTENT_WIDTH, TEXT_LG


def story_card(
    title: str,
    on_open: Callable[[], None],
    on_edit: Callable[[], None],
    on_delete: Callable[[], None],
) -> None:
    with ui.card().classes(CONTENT_WIDTH + " max-w-3xl"):
        with ui.row().classes("items-center justify-between"):
            ui.label(title).classes(TEXT_LG)
            with ui.row().classes("items-center gap-2"):
                ui.button("Continue", on_click=on_open)
                ui.button("Edit", on_click=on_edit)
                delete_dialog = confirm_delete_dialog(
                    "Delete story?",
                    "This will remove the story and its messages.",
                    on_confirm=on_delete,
                )
                ui.button(
                    "Delete",
                    color="negative",
                    on_click=delete_dialog.open,
                )
