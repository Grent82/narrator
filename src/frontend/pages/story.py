import asyncio
from typing import Callable

from httpx import AsyncClient, HTTPError
from nicegui import ui

from src.frontend.state import append_message, delete_story, get_story


def register_story_page(backend_url: str, log_error: Callable[[str], None]) -> None:
    @ui.page("/story/{story_id}")
    def story_page(story_id: str) -> None:
        story = get_story(story_id)
        if not story:
            ui.label("Story not found.").classes("text-lg text-red-500")
            ui.button("Back to stories", on_click=lambda: ui.navigate.to("/"))
            return

        with ui.row().classes("items-center justify-between w-full max-w-3xl"):
            ui.button("Back to stories", on_click=lambda: ui.navigate.to("/"))
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
                            on_click=lambda: (delete_story(story_id), ui.navigate.to("/")),
                        )
            ui.button("Delete", color="negative", on_click=delete_dialog.open)

        ui.label(str(story["title"])).classes("text-2xl font-semibold")

        story_log = ui.column().classes("w-full max-w-3xl gap-2")
        for msg in story["messages"]:
            if msg["role"] == "user":
                ui.label(f"> {msg['text']}").classes("text-gray-500")
            else:
                ui.label(msg["text"]).classes("whitespace-pre-wrap")

        busy_row = ui.row().classes("w-full max-w-3xl items-center gap-2")
        with busy_row:
            ui.spinner(size="md")
            ui.label("Processing your request...").classes("text-gray-500")
        if hasattr(busy_row, "set_visibility"):
            busy_row.set_visibility(False)
        else:
            busy_row.visible = False

        input_row = ui.row().classes("w-full max-w-3xl items-center gap-2")
        with input_row:
            input_field = ui.input("Command").props("autofocus").classes("flex-1")
            send_button = ui.button("Send")

        async def submit_command(_=None) -> None:
            cmd = (input_field.value or "").strip()
            if not cmd:
                return
            input_field.value = ""
            input_field.disable()
            send_button.disable()
            if hasattr(busy_row, "set_visibility"):
                busy_row.set_visibility(True)
            else:
                busy_row.visible = True

            append_message(story_id, "user", cmd)
            with story_log:
                ui.label(f"> {cmd}").classes("text-gray-500")

            assistant_text = ""
            append_message(story_id, "assistant", assistant_text)
            with story_log:
                response_label = ui.label("").classes("whitespace-pre-wrap")

            try:
                async with AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "POST",
                        f"{backend_url}/turn/stream",
                        json={"trigger": cmd},
                    ) as response:
                        response.raise_for_status()
                        buffer = ""
                    async for chunk in response.aiter_text():
                        if not chunk:
                            continue
                        buffer += chunk
                        if story.get("messages"):
                            story["messages"][-1]["text"] = buffer
                        response_label.set_text(buffer)
                        await asyncio.sleep(0)
            except HTTPError as exc:
                log_error(f"backend_http_error: {exc}")
                response_label.set_text(f"Backend error: {exc}")
            except Exception as exc:
                log_error(f"backend_unexpected_error: {exc}")
                response_label.set_text(f"Unexpected error: {exc}")
            finally:
                if hasattr(busy_row, "set_visibility"):
                    busy_row.set_visibility(False)
                else:
                    busy_row.visible = False
                input_field.enable()
                send_button.enable()

        send_button.on_click(submit_command)
        input_field.on("keydown.enter", submit_command)
