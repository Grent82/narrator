from typing import List, Tuple

from nicegui import ui

from src.frontend.ui_constants import DIALOG_INPUT, DIALOG_INPUT_PROPS


def parse_tags(value: str) -> List[str]:
    return [tag.strip() for tag in (value or "").split(",") if tag.strip()]


def story_details_fields(
    title: str,
    description: str,
    tags: List[str],
) -> Tuple[ui.input, ui.textarea, ui.input]:
    title_input = ui.input("Story title", value=title).props(f"autofocus {DIALOG_INPUT_PROPS}").classes(
        DIALOG_INPUT
    )
    description_input = (
        ui.textarea("Description", value=description)
        .props(f"autogrow {DIALOG_INPUT_PROPS}")
        .classes(DIALOG_INPUT)
    )
    tags_input = ui.input("Tags (comma-separated)", value=", ".join(tags)).props(DIALOG_INPUT_PROPS).classes(
        DIALOG_INPUT
    )
    return title_input, description_input, tags_input
