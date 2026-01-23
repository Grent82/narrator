from nicegui import ui

from src.frontend.components.dialogs import create_story_dialog
from src.frontend.components.empty_state import empty_state
from src.frontend.components.page_title import page_title
from src.frontend.components.story_card import story_card
from src.frontend.state import create_story, delete_story, get_story, list_story_ids


def register_index_page() -> None:
    @ui.page("/")
    def index_page() -> None:
        page_title("Stories")

        def open_story(story_id: str) -> None:
            ui.navigate.to(f"/story/{story_id}")

        def handle_create(title: str) -> None:
            story_id = create_story(title)
            ui.navigate.to(f"/story/{story_id}")

        def handle_delete(story_id: str) -> None:
            delete_story(story_id)
            ui.navigate.to("/")

        dialog = create_story_dialog(handle_create)

        with ui.row().classes("items-center gap-2"):
            ui.button("New story", on_click=dialog.open)

        story_ids = list_story_ids()
        if not story_ids:
            empty_state("No stories yet.")
            return

        for story_id in story_ids:
            story = get_story(story_id)
            if not story:
                continue
            story_card(
                str(story["title"]),
                on_open=lambda sid=story_id: open_story(sid),
                on_delete=lambda sid=story_id: handle_delete(sid),
            )
