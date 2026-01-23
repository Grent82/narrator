import os

from nicegui import ui

from src.frontend.pages.index import register_index_page
from src.frontend.pages.story import register_story_page
from src.shared.logging_config import configure_logging

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:17000")
FRONTEND_HOST = os.getenv("FRONTEND_HOST", "0.0.0.0")
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "17080"))
FRONTEND_LOG_FILE = os.getenv("FRONTEND_LOG_FILE", "logs/frontend.log")

logger = configure_logging(FRONTEND_LOG_FILE, "frontend")

register_index_page()
register_story_page(
    backend_url=BACKEND_URL,
    log_error=lambda message: logger.error(message),
)

ui.run(host=FRONTEND_HOST, port=FRONTEND_PORT)
