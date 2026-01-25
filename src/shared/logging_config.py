import logging
import os


def configure_logging(log_file: str, logger_name: str) -> logging.Logger:
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    level_name = (
        os.getenv(f"{logger_name.upper()}_LOG_LEVEL")
        or os.getenv("LOG_LEVEL")
        or "INFO"
    ).upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    # Reduce noise from file watcher used by NiceGUI/uvicorn reload.
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    return logging.getLogger(logger_name)
