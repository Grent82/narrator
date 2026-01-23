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
    with story_log:
        ui.label(f"> {cmd}").classes("text-gray-500")
    logger.info("submit_command len=%d", len(cmd))
    try:
        async with AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{BACKEND_URL}/turn", json={"trigger": cmd})
            response.raise_for_status()
            result = response.json().get("result", "")
    except HTTPError as exc:
        logger.exception("backend_http_error")
        result = f"Backend error: {exc}"
    except Exception as exc:  # NiceGUI should not crash on transient errors.
        logger.exception("backend_unexpected_error")
        result = f"Unexpected error: {exc}"
    with story_log:
        ui.label(result)

story_log = ui.column().classes("w-full max-w-3xl")
input_row = ui.row().classes("w-full max-w-3xl")
with input_row:
    input_field = ui.input("Command").props("autofocus").classes("flex-1")
    ui.button("Send", on_click=submit_command)
input_field.on("keydown.enter", submit_command)

ui.run(host=FRONTEND_HOST, port=FRONTEND_PORT)
