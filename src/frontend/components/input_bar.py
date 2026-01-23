from typing import Callable, Tuple

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, FLEX_1, ROW_GAP


def create_input_bar() -> Tuple[ui.input, ui.button]:
    row = ui.row().classes(f"{CONTENT_WIDTH} {ROW_GAP}")
    with row:
        input_field = ui.input("Command").props("autofocus").classes(FLEX_1)
        send_button = ui.button("Send")
    return input_field, send_button


def bind_input_actions(
    input_field: ui.input,
    send_button: ui.button,
    on_submit: Callable[[], None],
) -> None:
    send_button.on_click(on_submit)
    input_field.on("keydown.enter", on_submit)
