from nicegui import ui

from src.frontend.state import create_story, delete_story, get_story, list_story_ids


def register_index_page() -> None:
    @ui.page("/")
    def index_page() -> None:
        ui.label("Stories").classes("text-2xl font-semibold")

        def open_story(story_id: str) -> None:
            ui.navigate.to(f"/story/{story_id}")

        def handle_create(title: str, dialog) -> None:
            story_id = create_story(title)
            dialog.close()
            ui.navigate.to(f"/story/{story_id}")

        def handle_delete(story_id: str, dialog) -> None:
            delete_story(story_id)
            dialog.close()
            ui.navigate.to("/")

        dialog = ui.dialog()
        with dialog:
            with ui.card().classes("w-96"):
                ui.label("Create a new story").classes("text-lg font-semibold")
                title_input = ui.input("Story title").props("autofocus")
                with ui.row().classes("justify-end gap-2"):
                    ui.button("Cancel", on_click=dialog.close)
                    ui.button("Create", on_click=lambda: handle_create(title_input.value, dialog))

        with ui.row().classes("items-center gap-2"):
            ui.button("New story", on_click=dialog.open)

        story_ids = list_story_ids()
        if not story_ids:
            ui.label("No stories yet.").classes("text-gray-500")
            return

        for story_id in story_ids:
            story = get_story(story_id)
            if not story:
                continue
            with ui.card().classes("w-full max-w-3xl"):
                with ui.row().classes("items-center justify-between"):
                    ui.label(str(story["title"])).classes("text-lg")
                    with ui.row().classes("items-center gap-2"):
                        ui.button("Open", on_click=lambda _, sid=story_id: open_story(sid))
                        delete_dialog = ui.dialog()
                        with delete_dialog:
                            with ui.card().classes("w-96"):
                                ui.label("Delete story?").classes("text-lg font-semibold")
                                ui.label("This will remove the story and its messages.").classes("text-gray-500")
                                with ui.row().classes("justify-end gap-2"):
                                    ui.button("Cancel", on_click=delete_dialog.close)
                                    ui.button(
                                        "Delete",
                                        color="negative",
                                        on_click=lambda _, sid=story_id, dlg=delete_dialog: handle_delete(sid, dlg),
                                    )
                        ui.button(
                            "Delete",
                            color="negative",
                            on_click=delete_dialog.open,
                        )
