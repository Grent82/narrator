import asyncio
from typing import Callable

from httpx import HTTPError
from nicegui import ui

from src.frontend.components.busy_indicator import create_busy_indicator
from src.frontend.components.input_bar import bind_input_actions, create_input_bar
from src.frontend.services.backend_stream import stream_turn
from src.frontend.state import append_message, get_story


def create_story_actions(
    story_id: str,
    backend_url: str,
    log_error: Callable[[str], None],
    append_user_label: Callable[[str], None],
    append_assistant_label: Callable[[str], ui.label],
) -> None:
    _, show_busy, hide_busy = create_busy_indicator("Processing your request...")

    input_field, send_button = create_input_bar()

    async def submit_command(_=None) -> None:
        cmd = (input_field.value or "").strip()
        if not cmd:
            return
        input_field.value = ""
        input_field.disable()
        send_button.disable()
        show_busy()

        append_message(story_id, "user", cmd)
        append_user_label(cmd)

        append_message(story_id, "assistant", "")
        response_label = append_assistant_label("")

        try:
            buffer = ""
            async for chunk in stream_turn(backend_url, cmd, story_id=story_id):
                buffer += chunk
                story = get_story(story_id)
                if story and story.get("messages"):
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
            hide_busy()
            input_field.enable()
            send_button.enable()

    bind_input_actions(input_field, send_button, submit_command)
