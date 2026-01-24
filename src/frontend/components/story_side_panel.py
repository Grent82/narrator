from typing import Callable, Tuple

from nicegui import ui

from src.frontend.components.lore_tab import render_lore_tab
from src.frontend.components.plot_fields import PLOT_FIELD_DEFS, plot_field
from src.frontend.components.story_details_fields import parse_tags, story_details_fields
from src.frontend.state import update_story_field, update_story_metadata
from src.frontend.ui_constants import (
    SIDE_PANEL,
    SIDE_PANEL_PROPS,
    SIDE_PANEL_NAV,
    SIDE_PANEL_PANEL,
    SIDE_PANEL_TABS,
)


def create_story_side_panel(story: dict) -> Tuple[ui.element, Callable[[], None]]:
    drawer = ui.right_drawer().classes(SIDE_PANEL).props(SIDE_PANEL_PROPS)

    with drawer:
        with ui.column():

            with ui.row().classes(SIDE_PANEL_NAV):
                with ui.tabs().classes(SIDE_PANEL_TABS) as tabs:
                    tab_plot = ui.tab("Plot")
                    tab_lore = ui.tab("Lore")
                    tab_details = ui.tab("Details")

            with ui.tab_panels(tabs, value=tab_plot).classes(SIDE_PANEL_PANEL):
                with ui.tab_panel(tab_plot).classes("w-full q-pa-none"):
                    ai_def = PLOT_FIELD_DEFS["ai_instructions"]
                    summary_def = PLOT_FIELD_DEFS["plot_summary"]
                    essentials_def = PLOT_FIELD_DEFS["plot_essentials"]
                    author_def = PLOT_FIELD_DEFS["author_note"]

                    plot_field(
                        title=ai_def.title,
                        help_text=ai_def.help_text(editable=False),
                        value=story.get("ai_instructions", ""),
                        readonly=True,
                    )

                    plot_field(
                        title=summary_def.title,
                        help_text=summary_def.help_text(editable=False),
                        value=story.get("plot_summary", ""),
                        readonly=True,
                    )

                    plot_field(
                        title=essentials_def.title,
                        help_text=essentials_def.help_text(editable=True),
                        value=story.get("plot_essentials", ""),
                        readonly=False,
                        on_change=lambda value: update_story_field(story["id"], "plot_essentials", value),
                    )

                    plot_field(
                        title=author_def.title,
                        help_text=author_def.help_text(editable=True),
                        value=story.get("author_note", ""),
                        readonly=False,
                        on_change=lambda value: update_story_field(story["id"], "author_note", value),
                    )
                with ui.tab_panel(tab_lore).classes("w-full q-pa-none"):
                    render_lore_tab(story["id"])
                with ui.tab_panel(tab_details).classes("w-full q-pa-none"):
                    with ui.column().classes("w-full items-stretch gap-4"):
                        title_input, description_input, tags_input = story_details_fields(
                            str(story.get("title", "")),
                            str(story.get("description", "")),
                            list(story.get("tags", [])),
                        )

                    def sync_details() -> None:
                        update_story_metadata(
                            story["id"],
                            title_input.value or "",
                            description_input.value or "",
                            parse_tags(tags_input.value or ""),
                        )

                    title_input.on("change", lambda e: sync_details())
                    description_input.on("change", lambda e: sync_details())
                    tags_input.on("change", lambda e: sync_details())

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
