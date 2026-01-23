import asyncio
import os

from httpx import AsyncClient, HTTPError
from nicegui import ui 

from src.shared.logging_config import configure_logging

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:17000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "17080"))
FRONTEND_LOG_FILE = os.getenv("FRONTEND_LOG_FILE", "logs/frontend.log")

logger = configure_logging(FRONTEND_LOG_FILE, "frontend")

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
    with story_log:
        ui.label(f"> {cmd}").classes("text-gray-500")
    logger.info("submit_command len=%d", len(cmd))
    response_label = None
    with story_log:
        response_label = ui.label("").classes("whitespace-pre-wrap")
    try:
        async with AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{BACKEND_URL}/turn/stream",
                json={"trigger": cmd},
            ) as response:
                response.raise_for_status()
                buffer = ""
                async for chunk in response.aiter_text():
                    if not chunk:
                        continue
                    buffer += chunk
                    response_label.set_text(buffer)
                    await asyncio.sleep(0)
    except HTTPError as exc:
        logger.exception("backend_http_error")
        response_label.set_text(f"Backend error: {exc}")
    except Exception as exc:  # NiceGUI should not crash on transient errors.
        logger.exception("backend_unexpected_error")
        response_label.set_text(f"Unexpected error: {exc}")
    finally:
        if hasattr(busy_row, "set_visibility"):
            busy_row.set_visibility(False)
        else:
            busy_row.visible = False
        input_field.enable()
        send_button.enable()

story_log = ui.column().classes("w-full max-w-3xl")
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
    send_button = ui.button("Send", on_click=submit_command)
input_field.on("keydown.enter", submit_command)

ui.run(host=FRONTEND_HOST, port=FRONTEND_PORT)
