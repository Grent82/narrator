from dataclasses import dataclass
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


@dataclass(frozen=True)
class PlotFieldDef:
    key: str
    title: str
    help_readonly: str
    help_editable: str

    def help_text(self, editable: bool) -> str:
        return self.help_editable if editable else self.help_readonly


PLOT_FIELD_DEFS = {
    "ai_instructions": PlotFieldDef(
        key="ai_instructions",
        title="AI Instructions",
        help_readonly="System-level guidance created at story start. Not editable during play.",
        help_editable="Guidance created at story start. You can adjust it before play.",
    ),
    "plot_summary": PlotFieldDef(
        key="plot_summary",
        title="Plot Summary",
        help_readonly="Short LLM-written summary to keep the story on track. Not editable.",
        help_editable="Short LLM-written summary to keep the story on track.",
    ),
    "plot_essentials": PlotFieldDef(
        key="plot_essentials",
        title="Plot Essentials",
        help_readonly="Key background facts always relevant.",
        help_editable="Key background facts always relevant. You can extend this.",
    ),
    "author_note": PlotFieldDef(
        key="author_note",
        title="Author's Note",
        help_readonly="Short-term tone and style guidance for the AI.",
        help_editable="Short-term tone and style guidance for the AI. Editable.",
    ),
}


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
        textarea.on("change", lambda _: on_change(textarea.value or ""))

    return textarea
