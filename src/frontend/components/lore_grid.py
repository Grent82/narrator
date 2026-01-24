from typing import Callable, Dict, List

from nicegui import ui

from src.frontend.ui_constants import (
    LORE_ADD_CARD,
    LORE_ADD_ICON,
    LORE_ADD_TEXT,
    LORE_CARD,
    LORE_CARD_BODY,
    LORE_CARD_TITLE,
    LORE_GRID,
    LORE_MENU_BUTTON,
    LORE_TAG,
)


def render_lore_grid(
    container: ui.element,
    entries: List[Dict[str, str]],
    on_add: Callable[[], None],
    on_edit: Callable[[Dict[str, str]], None],
    on_delete: Callable[[Dict[str, str]], None],
    on_duplicate: Callable[[Dict[str, str]], None],
) -> None:
    container.clear()
    with container:
        with ui.element("div").classes(LORE_GRID):
            with ui.card().classes(LORE_ADD_CARD).on("click", lambda _: on_add()):
                ui.label("+").classes(LORE_ADD_ICON)
                ui.label("Add character info, location, faction, and more").classes(LORE_ADD_TEXT)

            for entry in entries:
                with ui.card().classes(LORE_CARD):
                    ui.label(entry.get("title", "")).classes(LORE_CARD_TITLE)
                    ui.label(entry.get("description", "")).classes(LORE_CARD_BODY)
                    with ui.row().classes("items-center mt-auto"):
                        ui.label(entry.get("tag", "")).classes(LORE_TAG)
                        ui.element("div").classes("flex-1")
                        menu_button = ui.button(icon="more_horiz").props("flat dense").classes(LORE_MENU_BUTTON)
                        with ui.menu() as menu:
                            ui.menu_item("Edit", on_click=lambda _, e=entry: on_edit(e))
                            ui.menu_item("Duplicate", on_click=lambda _, e=entry: on_duplicate(e))
                            ui.menu_item("Delete", on_click=lambda _, e=entry: on_delete(e))
                        menu_button.on("click", menu.open)
