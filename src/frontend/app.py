from nicegui import ui

from src.frontend.config import BACKEND_URL, FRONTEND_HOST, FRONTEND_LOG_FILE, FRONTEND_PORT
from src.frontend.pages.index import register_index_page
from src.frontend.pages.story import register_story_page
from src.shared.logging_config import configure_logging

logger = configure_logging(FRONTEND_LOG_FILE, "frontend")

register_index_page()
register_story_page(
    backend_url=BACKEND_URL,
    log_error=lambda message: logger.error(message),
)

ui.run(host=FRONTEND_HOST, port=FRONTEND_PORT)
