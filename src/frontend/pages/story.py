from typing import Callable

from nicegui import ui

from src.frontend.components.chat_log import create_chat_log
from src.frontend.components.story_actions import create_story_actions
from src.frontend.components.story_header import story_header
from src.frontend.components.story_side_panel import create_story_side_panel
from src.frontend.state import get_story, invalidate_story_cache, sync_story_lore


def register_story_page(backend_url: str, log_error: Callable[[str], None]) -> None:
    
    @ui.page("/story/{story_id}")
    def story_page(story_id: str) -> None:
        sync_story_lore(story_id)
        invalidate_story_cache(story_id)
        story = get_story(story_id)
        if not story:
            ui.label("Story not found.").classes("text-lg text-red-500")
            ui.button("Back to stories", on_click=lambda: ui.navigate.to("/"))
            return

        _, toggle_panel = create_story_side_panel(story)

        with ui.column().classes("w-full items-center"):
            story_header(
                str(story["title"]),
                on_back=lambda: ui.navigate.to("/"),
                on_settings=toggle_panel,
                review_items=story.get("lore_review", []),
                story_id=story_id,
            )

            _, append_user, append_assistant, render_messages = create_chat_log(story.get("messages", []))

            create_story_actions(
                story_id=story_id,
                backend_url=backend_url,
                log_error=log_error,
                append_user_label=append_user,
                append_assistant_label=append_assistant,
                render_messages=render_messages,
            )
