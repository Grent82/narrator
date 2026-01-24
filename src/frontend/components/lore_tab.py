from typing import Callable, Dict, List

from nicegui import ui

from src.frontend.state import add_lore_entry, delete_lore_entry, list_lore, update_lore_entry
from src.frontend.ui_constants import (
    DIALOG_ACTIONS,
    DIALOG_BODY,
    DIALOG_CARD,
    DIALOG_INPUT,
    DIALOG_INPUT_PROPS,
    DIALOG_TITLE,
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


def _render_lore_grid(
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


def render_lore_tab(story_id: str) -> None:
    tag_options = ["NPC", "Place", "Race", "Event", "Faction", "Custom"]

    def refresh() -> None:
        _render_lore_grid(
            grid_container,
            list_lore(story_id),
            open_add_dialog,
            open_edit_dialog,
            handle_delete,
            handle_duplicate,
        )

    def _set_form_values(title: str, description: str, tag: str | None, triggers: str) -> None:
        title_input.value = title
        description_input.value = description
        triggers_input.value = triggers
        tag_value = None
        if tag:
            for option in tag_options:
                if option.lower() == tag.lower():
                    tag_value = option
                    break
        tag_input.value = tag_value
        title_input.update()
        description_input.update()
        triggers_input.update()
        tag_input.update()

    def open_add_dialog() -> None:
        edit_state["entry_id"] = ""
        _set_form_values("", "", None, "")
        dialog_title_label.text = "New Lore Entry"
        dialog_title_label.update()
        dialog.open()

    edit_state = {"entry_id": ""}

    def open_edit_dialog(entry: Dict[str, str]) -> None:
        edit_state["entry_id"] = entry.get("id", "")
        _set_form_values(
            entry.get("title", ""),
            entry.get("description", ""),
            entry.get("tag", ""),
            entry.get("triggers", ""),
        )
        dialog_title_label.text = entry.get("title", "") or "Lore Entry"
        dialog_title_label.update()
        dialog.open()

    def handle_save() -> None:
        entry_id = edit_state.get("entry_id", "")
        if entry_id:
            update_lore_entry(
                story_id,
                entry_id,
                title_input.value or "",
                description_input.value or "",
                tag_input.value or "",
                triggers_input.value or "",
            )
        else:
            add_lore_entry(
                story_id,
                title_input.value or "",
                description_input.value or "",
                tag_input.value or "",
                triggers_input.value or "",
            )
        edit_state["entry_id"] = ""
        dialog.close()
        refresh()

    def handle_delete(entry: Dict[str, str]) -> None:
        delete_lore_entry(story_id, entry.get("id", ""))
        refresh()

    def handle_duplicate(entry: Dict[str, str]) -> None:
        add_lore_entry(
            story_id,
            entry.get("title", ""),
            entry.get("description", ""),
            entry.get("tag", ""),
            entry.get("triggers", ""),
        )
        refresh()

    dialog = ui.dialog()
    with dialog:
        with ui.card().classes(DIALOG_CARD):
            with ui.column().classes(DIALOG_BODY):
                dialog_title_label = ui.label("Lore Entry").classes(DIALOG_TITLE)
                title_input = ui.input("Title").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                description_input = (
                    ui.textarea("Description")
                    .props(f"autogrow {DIALOG_INPUT_PROPS}")
                    .classes(DIALOG_INPUT)
                )
                triggers_input = ui.input("Triggers").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                tag_input = ui.select(tag_options, label="Tag").props(DIALOG_INPUT_PROPS).classes(DIALOG_INPUT)
                with ui.row().classes(DIALOG_ACTIONS):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=handle_save)

    def sync_title_label(value: str) -> None:
        if edit_state.get("entry_id"):
            dialog_title_label.text = value or "Lore Entry 1"
        else:
            dialog_title_label.text = value or "New Lore Entry 2"
        dialog_title_label.update()

    title_input.on("input", lambda e: sync_title_label(e.value))

    grid_container = ui.element("div").classes("w-full")
    refresh()
