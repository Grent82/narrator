from typing import Callable, Optional

from nicegui import ui

from src.frontend.ui_constants import (
    COMPONENT_CONTAINER,
    COMPONENT_HELP,
    COMPONENT_INPUT,
    COMPONENT_INPUT_CLASS,
    COMPONENT_INPUT_STYLE,
    COMPONENT_TITLE,
)

def plot_field(
    title: str,
    help_text: str,
    value: str,
    readonly: bool,
    on_change: Optional[Callable[[str], None]] = None,
) -> ui.textarea:
    with ui.column().classes(COMPONENT_CONTAINER):
        ui.label(title).classes(COMPONENT_TITLE)
        help_label = ui.label(help_text).classes(COMPONENT_HELP)
        textarea = (
            ui.textarea(value=value)
            .classes(COMPONENT_INPUT)
            .props("autogrow")
            .props(f"input-class={COMPONENT_INPUT_CLASS} input-style={COMPONENT_INPUT_STYLE}")
        )
    if readonly:
        textarea.props("readonly")

    def show_when_empty(text: str) -> bool:
        return not (text or "").strip()

    help_label.bind_visibility_from(textarea, "value", backward=show_when_empty)

    if on_change:
        textarea.on("change", lambda e: on_change(e.value))

    return textarea
