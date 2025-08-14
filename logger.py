"""Centralized logging configuration for workshop-watcher."""
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    log_level: str = "DEBUG",
    console_output: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up centralized logging for the workshop-watcher application.
    
    Args:
        log_file: Path to log file. If None, defaults to workshop-watcher.log
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to also output to console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    # Set default log file if not provided
    if log_file is None:
        log_file = "workshop-watcher.log"
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger("workshop-watcher")
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add file handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError) as e:
        # Can't use logger here since we're setting it up
        if console_output:
            print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        # Use simpler format for console
        console_formatter = logging.Formatter(
            fmt='%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    logger.info("Logging initialized")
    return logger


def get_logger(name: str = "workshop-watcher") -> logging.Logger:
    """Get logger instance. Sets up logging if not already configured."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Setup default logging if not already configured
        setup_logging()
    return logger


# Module-level convenience function
def log_exception(logger: logging.Logger, message: str, exc_info: bool = True) -> None:
    """Log an exception with traceback."""
    logger.error(message, exc_info=exc_info)
