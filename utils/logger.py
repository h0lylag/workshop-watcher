"""Centralized logging configuration for workshop-watcher (console / journal only)."""
import logging
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
) -> logging.Logger:
    """Configure a console-only logger (systemd will capture stdout/stderr)."""
    logger = logging.getLogger("workshop-watcher")
    # Reset handlers so repeated calls (e.g. tests) don't duplicate output
    logger.handlers.clear()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(module)s:%(lineno)d - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Logging initialized (console only)")
    return logger


def get_logger(name: str = "workshop-watcher") -> logging.Logger:
    """Return existing logger (assumes setup_logging called in main)."""
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    logger.error(message, exc_info=exc_info)
