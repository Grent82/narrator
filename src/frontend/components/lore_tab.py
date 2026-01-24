from typing import Dict, List

from nicegui import ui

from src.frontend.components.lore_grid import render_lore_grid
from src.frontend.state import add_lore_entry, delete_lore_entry, list_lore, update_lore_entry
from src.frontend.ui_constants import (
    DIALOG_ACTIONS,
    DIALOG_BODY,
    DIALOG_CARD,
    DIALOG_INPUT,
    DIALOG_INPUT_PROPS,
    DIALOG_TITLE,
)
from src.shared.lore_tags import LORE_TAG_OPTIONS


def render_lore_tab(story_id: str) -> None:
    tag_options = LORE_TAG_OPTIONS

    def refresh() -> None:
        render_lore_grid(
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
        if tag and not tag_value:
            tag_value = "Custom"
            custom_tag_input.value = tag
        else:
            custom_tag_input.value = ""
        tag_input.value = tag_value
        toggle_custom(tag_value)
        title_input.update()
        description_input.update()
        triggers_input.update()
        custom_tag_input.update()
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
                custom_tag_input.value if tag_input.value == "Custom" else (tag_input.value or ""),
                triggers_input.value or "",
            )
        else:
            add_lore_entry(
                story_id,
                title_input.value or "",
                description_input.value or "",
                custom_tag_input.value if tag_input.value == "Custom" else (tag_input.value or ""),
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
                custom_tag_input = (
                    ui.input("Custom tag")
                    .props(f"{DIALOG_INPUT_PROPS} placeholder=Enter a custom type...")
                    .classes(DIALOG_INPUT)
                )
                if hasattr(custom_tag_input, "set_visibility"):
                    custom_tag_input.set_visibility(False)
                else:
                    custom_tag_input.visible = False
                with ui.row().classes(DIALOG_ACTIONS):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Save", on_click=handle_save)

    def sync_title_label(value: str) -> None:
        if edit_state.get("entry_id"):
            dialog_title_label.text = value or "Lore Entry"
        else:
            dialog_title_label.text = value or "New Lore Entry"
        dialog_title_label.update()

    title_input.on("input", lambda e: sync_title_label(e.value))
    def toggle_custom(value: str | None) -> None:
        is_custom = value == "Custom"
        if hasattr(custom_tag_input, "set_visibility"):
            custom_tag_input.set_visibility(is_custom)
        else:
            custom_tag_input.visible = is_custom
        if not is_custom:
            custom_tag_input.value = ""
            custom_tag_input.update()

    tag_input.on("update:model-value", lambda e: toggle_custom(tag_input.value))
    tag_input.on("change", lambda e: toggle_custom(tag_input.value))

    grid_container = ui.element("div").classes("w-full")
    refresh()
