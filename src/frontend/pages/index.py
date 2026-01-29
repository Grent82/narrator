from nicegui import ui

from src.frontend.components.dialogs import create_story_dialog, edit_story_dialog
from src.frontend.components.empty_state import empty_state
from src.frontend.components.page_title import page_title
from src.frontend.components.story_card import story_card
from src.frontend.state import create_story, delete_story, get_story, list_story_ids, sync_story_lore, update_story_from_editor


def register_index_page() -> None:
    @ui.page("/")
    def index_page() -> None:
        with ui.row().classes("w-full justify-center"):
            page_title("Stories")

        def open_story(story_id: str) -> None:
            sync_story_lore(story_id)
            ui.navigate.to(f"/story/{story_id}")

        def handle_create(
            title: str,
            preset_key: str,
            ai_instructions: str,
            plot_essentials: str,
            author_note: str,
            description: str,
            tags: list[str],
            lore_entries: list[dict[str, str]],
        ) -> None:
            story_id = create_story(
                title=title,
                ai_instruction_key=preset_key,
                ai_instructions=ai_instructions,
                plot_essentials=plot_essentials,
                author_note=author_note,
                description=description,
                tags=tags,
                lore_entries=lore_entries,
            )
            ui.navigate.to(f"/story/{story_id}")

        def handle_delete(story_id: str) -> None:
            delete_story(story_id)
            ui.navigate.to("/")

        def handle_edit(
            story_id: str,
            title: str,
            preset_key: str,
            ai_instructions: str,
            plot_essentials: str,
            author_note: str,
            description: str,
            tags: list[str],
            lore_entries: list[dict[str, str]],
        ) -> None:
            update_story_from_editor(
                story_id,
                title,
                preset_key,
                ai_instructions,
                plot_essentials,
                author_note,
                description,
                tags,
                lore_entries,
            )
            ui.navigate.to("/")

        dialog = create_story_dialog(handle_create)

        with ui.row().classes("w-full justify-center"):
            ui.button("New story", on_click=dialog.open)

        with ui.column().classes("w-full items-center"):
            story_ids = list_story_ids()
            if not story_ids:
                empty_state("No stories yet.")
                return

            for story_id in story_ids:
                story = get_story(story_id)
                if not story:
                    continue
                edit_dialog = edit_story_dialog(
                    story,
                    on_save=lambda title, preset, ai, essentials, author_note, description, tags, lore, sid=story_id: (
                        handle_edit(sid, title, preset, ai, essentials, author_note, description, tags, lore)
                    ),
                )
                story_card(
                    str(story["title"]),
                    on_open=lambda sid=story_id: open_story(sid),
                    on_edit=edit_dialog.open,
                    on_delete=lambda sid=story_id: handle_delete(sid),
                )
