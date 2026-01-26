import asyncio
from typing import Callable

from httpx import HTTPError
from nicegui import ui

from src.frontend.components.busy_indicator import create_busy_indicator
from src.frontend.components.input_bar import bind_input_actions, create_input_bar
from src.frontend.services.backend_stream import stream_turn
from src.frontend.state import (
    append_message,
    append_message_with_mode,
    get_story_messages,
    update_last_message,
    update_story_messages,
)


def create_story_actions(
    story_id: str,
    backend_url: str,
    log_error: Callable[[str], None],
    append_user_label: Callable[[str, str | None], None],
    append_assistant_label: Callable[[str], ui.label],
    render_messages: Callable[[list], None],
) -> None:
    _, show_busy, hide_busy = create_busy_indicator("Processing your request...")

    action_wrapper = ui.row().classes("w-full justify-center max-w-3xl")
    with action_wrapper:
        action_row = ui.row().classes("items-center gap-2")
        with action_row:
            take_turn_button = ui.button("Take a Turn").props("outline dense")
            continue_button = ui.button("Continue").props("outline dense")
            retry_button = ui.button("Retry").props("outline dense")
            erase_button = ui.button("Erase").props("outline dense")

    input_field, send_button, mode_state, input_container, close_button = create_input_bar()
    input_container.set_visibility(False)

    def show_input_mode() -> None:
        action_wrapper.set_visibility(False)
        input_container.set_visibility(True)
        if hasattr(input_field, "run_method"):
            input_field.run_method("focus")

    def show_action_mode() -> None:
        input_container.set_visibility(False)
        action_wrapper.set_visibility(True)

    async def persist_messages() -> None:
        messages_snapshot = [dict(msg) for msg in get_story_messages(story_id)]
        await asyncio.to_thread(update_story_messages, story_id, messages_snapshot)

    take_turn_button.on_click(show_input_mode)
    close_button.on_click(show_action_mode)

    async def send_turn(text: str, mode: str, show_user: bool = True) -> None:
        input_field.value = ""
        input_field.disable()
        send_button.disable()
        show_busy()

        if show_user:
            append_message_with_mode(story_id, "user", text, mode)
            append_user_label(text, mode)

        append_message(story_id, "assistant", "")
        response_label = append_assistant_label("")

        try:
            buffer = ""
            async for chunk in stream_turn(backend_url, text, mode, story_id=story_id):
                buffer += chunk
                update_last_message(story_id, buffer)
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
            show_action_mode()
            await persist_messages()

    async def submit_command(_=None) -> None:
        cmd = (input_field.value or "").strip()
        if not cmd:
            return
        mode = mode_state.get("mode", "story")
        await send_turn(cmd, mode, show_user=True)

    def _find_last_user(messages: list[dict]) -> dict | None:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg
        return None

    async def handle_continue() -> None:
        await send_turn("", "continue", show_user=False)

    async def handle_retry() -> None:
        messages = get_story_messages(story_id)
        if not messages:
            return
        last_role = messages[-1].get("role")
        if last_role == "assistant":
            messages.pop()
            render_messages(messages)
            last_user = _find_last_user(messages)
            if last_user:
                await send_turn(last_user.get("text", ""), last_user.get("mode", "story"), show_user=False)
            else:
                await send_turn("", "continue", show_user=False)
            return
        if last_role == "user":
            await send_turn(messages[-1].get("text", ""), messages[-1].get("mode", "story"), show_user=False)

    def handle_erase() -> None:
        messages = get_story_messages(story_id)
        if not messages:
            return
        messages.pop()
        render_messages(messages)
        asyncio.create_task(persist_messages())

    bind_input_actions(input_field, send_button, submit_command)
    continue_button.on_click(lambda: asyncio.create_task(handle_continue()))
    retry_button.on_click(lambda: asyncio.create_task(handle_retry()))
    erase_button.on_click(handle_erase)
