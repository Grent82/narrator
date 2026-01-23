from typing import Callable

from nicegui import ui

from src.frontend.ui_constants import CARD_WIDTH, ROW_END, SECTION_TITLE, TEXT_MUTED


def create_story_dialog(on_create: Callable[[str], None]) -> ui.dialog:
    dialog = ui.dialog()
    with dialog:
        with ui.card().classes(CARD_WIDTH):
            ui.label("Create a new story").classes(SECTION_TITLE)
            title_input = ui.input("Story title").props("autofocus")
            with ui.row().classes(ROW_END):
                ui.button("Cancel", on_click=dialog.close)
                ui.button(
                    "Create",
                    on_click=lambda: (on_create(title_input.value), dialog.close()),
                )
    return dialog


def confirm_delete_dialog(
    title: str,
    message: str,
    on_confirm: Callable[[], None],
) -> ui.dialog:
    dialog = ui.dialog()
    with dialog:
        with ui.card().classes(CARD_WIDTH):
            ui.label(title).classes(SECTION_TITLE)
            ui.label(message).classes(TEXT_MUTED)
            with ui.row().classes(ROW_END):
                ui.button("Cancel", on_click=dialog.close)
                ui.button(
                    "Delete",
                    color="negative",
                    on_click=lambda: (on_confirm(), dialog.close()),
                )
    return dialog
