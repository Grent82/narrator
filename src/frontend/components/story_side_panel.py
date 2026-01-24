from typing import Callable, Tuple

from nicegui import ui

from src.frontend.components.plot_fields import plot_field
from src.frontend.state import update_story_field
from src.frontend.ui_constants import (
    SIDE_PANEL,
    SIDE_PANEL_PROPS,
    SIDE_PANEL_NAV,
    SIDE_PANEL_PANEL,
    SIDE_PANEL_SECTION,
    SIDE_PANEL_TABS,
)


def create_story_side_panel(story: dict) -> Tuple[ui.element, Callable[[], None]]:
    drawer = ui.right_drawer().classes(SIDE_PANEL).props(SIDE_PANEL_PROPS)
    tabs_id = f"story-tabs-{story.get('id', 'default')}"

    def scroll_tabs(delta: int) -> None:
        ui.run_javascript(
            f"const el=document.getElementById('{tabs_id}'); if (el) el.scrollLeft += {delta};"
        )

    with drawer:
        with ui.column():

            with ui.row().classes(SIDE_PANEL_NAV):
                with ui.tabs().classes(SIDE_PANEL_TABS) as tabs:
                    tab_plot = ui.tab("Plot")
                    tab_lore = ui.tab("Lore")
                    tab_settings = ui.tab("Settings")

            with ui.tab_panels(tabs, value=tab_plot).classes(SIDE_PANEL_PANEL):
                with ui.tab_panel(tab_plot).classes("w-full q-pa-none"):
                    plot_field(
                        title="AI Instructions",
                        help_text="System-level guidance created at story start. Not editable during play.",
                        value=story.get("ai_instructions", ""),
                        readonly=True,
                    )

                    plot_field(
                        title="Plot Summary",
                        help_text="Short LLM-written summary to keep the story on track. Not editable.",
                        value=story.get("plot_summary", ""),
                        readonly=True,
                    )

                    plot_field(
                        title="Plot Essentials",
                        help_text="Key background facts always relevant. You can extend this.",
                        value=story.get("plot_essentials", ""),
                        readonly=False,
                        on_change=lambda value: update_story_field(story["id"], "plot_essentials", value),
                    )

                    plot_field(
                        title="Author's Note",
                        help_text="Short-term tone and style guidance for the AI. Editable.",
                        value=story.get("author_note", ""),
                        readonly=False,
                        on_change=lambda value: update_story_field(story["id"], "author_note", value),
                    )
                with ui.tab_panel(tab_lore).classes("w-full q-pa-none"):
                    ui.label("Lore overview goes here.").classes(SIDE_PANEL_SECTION)
                with ui.tab_panel(tab_settings).classes("w-full q-pa-none"):
                    ui.label("Story settings go here.").classes(SIDE_PANEL_SECTION)

    if hasattr(drawer, "value"):
        drawer.value = False

    def toggle() -> None:
        if hasattr(drawer, "toggle"):
            drawer.toggle()
        elif getattr(drawer, "value", False):
            drawer.close()
        else:
            drawer.open()

    return drawer, toggle
