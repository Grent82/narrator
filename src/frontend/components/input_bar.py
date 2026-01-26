from typing import Callable, Tuple

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, FLEX_1, ROW_GAP


def create_input_bar() -> Tuple[ui.input, ui.button, dict, ui.element, ui.button]:
    modes = [
        ("do", "Do", "What do you do?"),
        ("say", "Say", "What do you say?"),
        ("story", "Story", "What happens next?"),
    ]
    placeholders = {key: placeholder for key, _, placeholder in modes}
    mode_state = {"mode": "story"}
    input_field = None

    def set_mode(key: str, placeholder: str) -> None:
        mode_state["mode"] = key
        if input_field:
            input_field.props(f'placeholder="{placeholder}"')
            input_field.update()

    container = ui.column().classes(f"{CONTENT_WIDTH} gap-2  max-w-3xl")
    with container:
        with ui.row().classes("items-center gap-2"):
            close_button = ui.button("✕").props("outline dense")
            tabs = ui.tabs(
                value="story",
                on_change=lambda e: set_mode(e.value, placeholders.get(e.value, "")),
            )
            with tabs:
                for key, label, _ in modes:
                    ui.tab(key, label=label)
        with ui.row().classes(f"{ROW_GAP} w-full"):
            input_field = ui.input().props("autofocus").classes(FLEX_1)
            send_button = ui.button("Send")

    set_mode("story", "What happens next?")
    return input_field, send_button, mode_state, container, close_button


def bind_input_actions(
    input_field: ui.input,
    send_button: ui.button,
    on_submit: Callable[[], None],
) -> None:
    send_button.on_click(on_submit)
    input_field.on("keydown.enter", on_submit)
