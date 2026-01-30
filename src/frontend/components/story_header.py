from typing import Callable, Optional

from nicegui import ui

from src.frontend.ui_constants import CONTENT_WIDTH, TITLE
from src.frontend.state import accept_lore_suggestion, reject_lore_suggestion


def story_header(
    title: str,
    on_back: Callable[[], None],
    on_settings: Optional[Callable[[], None]] = None,
    review_items: Optional[list[dict]] = None,
    story_id: Optional[str] = None,
) -> None:
    pending = review_items or []
    with ui.column().classes(
        f"{CONTENT_WIDTH} sticky top-0 z-10 bg-slate-950/90 backdrop-blur border-b border-slate-800/60 py-2"
    ):
        with ui.row().classes(f"{CONTENT_WIDTH}"):
            ui.button("Back to stories", on_click=on_back)
        with ui.row().classes(f"{CONTENT_WIDTH} items-center justify-center gap-2"):
            ui.label(title).classes(f"{TITLE} text-center")
            if on_settings:
                with ui.element("div").classes("relative"):
                    review_button = ui.button(icon="playlist_add_check").props("flat")
                    if pending:
                        ui.badge(str(len(pending))).props("color=red").classes("absolute -top-1 -right-1 text-xs")
                    with review_button:
                        review_menu = ui.menu()
                        with review_menu:
                            ui.label("Lore Review").classes("font-semibold px-2")
                            if not pending:
                                ui.label("No new lore suggestions.").classes("text-sm text-slate-400 px-2")
                            else:
                                for item in pending:
                                    title_text = str(item.get("title", "Untitled"))
                                    kind = str(item.get("tag", ""))
                                    status = str(item.get("kind", "NEW")).upper()
                                    suggestion_id = str(item.get("id", ""))
                                    with ui.card().classes("w-80"):
                                        ui.label(f"[{status}] {title_text}").classes("font-semibold")
                                        if kind:
                                            ui.label(kind).classes("text-xs text-slate-400")
                                        description = str(item.get("description", "")).strip()
                                        if description:
                                            ui.label(description).classes("text-sm")
                                        with ui.row().classes("gap-2"):
                                            def _accept(sid: str = suggestion_id) -> None:
                                                if story_id and sid:
                                                    accept_lore_suggestion(story_id, sid)
                                                    ui.navigate.to(f"/story/{story_id}")
                                            def _reject(sid: str = suggestion_id) -> None:
                                                if story_id and sid:
                                                    reject_lore_suggestion(story_id, sid)
                                                    ui.navigate.to(f"/story/{story_id}")
                                            ui.button("Accept", on_click=_accept).props("dense outline")
                                            ui.button("Edit", on_click=lambda: ui.notify("Edit not wired yet")).props("dense outline")
                                            ui.button("Reject", on_click=_reject).props("dense outline")
                    review_button.on_click(review_menu.open)
                ui.button(icon="settings", on_click=on_settings).props("flat")
