from typing import Callable, Tuple

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, ROW_GAP, TEXT_MUTED


def create_busy_indicator(label: str) -> Tuple[ui.row, Callable[[], None], Callable[[], None]]:
    row = ui.row().classes(f"{CONTENT_WIDTH} {ROW_GAP}  max-w-3xl justify-center")
    with row:
        ui.spinner(size="md")
        ui.label(label).classes(TEXT_MUTED)

    def set_visible(value: bool) -> None:
        if hasattr(row, "set_visibility"):
            row.set_visibility(value)
        else:
            row.visible = value

    set_visible(False)
    return row, lambda: set_visible(True), lambda: set_visible(False)
