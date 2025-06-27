"""
Global logging configuration used by both the test-runner and the demo API.
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Always use absolute path relative to project root
PROJECT_ROOT = Path(__file__).parent.parent  # Go up from utils/ to project root
LOG_DIR = PROJECT_ROOT / "logs"

LOG_MESSAGE_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
LOG_TIME_FORMAT = "%H:%M:%S"


class _ColourFormatter(logging.Formatter):
    """Formatter that adds colors to levelname only for console output."""
    COLOURS = {"DEBUG": 37, "INFO": 36, "WARNING": 33, "ERROR": 31, "CRITICAL": 41}
    RESET = "\033[0m"

    def format(self, record):
        original_levelname = record.levelname  # Save original levelname
        colour_code = self.COLOURS.get(
            record.levelname, ""
        )  # Add color only for formatting
        if colour_code:
            record.levelname = f"\033[{colour_code}m{record.levelname}{self.RESET}"
        result = super().format(record=record)
        record.levelname = original_levelname  # Restore original levelname
        return result


def configure_logging(
    *,
    level: str = "INFO",
    logfile_path: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """Initialise the *root* logger exactly once.

    Arguments
    ---------
    level         : Root log-level (e.g. "DEBUG", "INFO").
    logfile_path  : Path of the session-wide log file. If None → default to 'logs/test_<timestamp>.log'.
    enable_console: If True a colourised StreamHandler is attached to stdout.

    Raises
    ------
    OSError: If the logs directory cannot be created or accessed.
    """
    root_logger = logging.getLogger()
    if root_logger.handlers:  # Already configured? Then do nothing.
        return

    root_logger.setLevel(level.upper())

    # Ensure logs directory exists at project root
    try:
        LOG_DIR.mkdir(exist_ok=True)
    except (PermissionError, OSError) as e:
        raise OSError(
            f"Cannot create logs directory at {LOG_DIR}. Ensure you have write permissions: {e}"
        )

    # Create plain formatter for file output
    plain_formatter = logging.Formatter(fmt=LOG_MESSAGE_FORMAT, datefmt=LOG_TIME_FORMAT)

    # Set default log file path if not provided
    if not logfile_path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        logfile_path = str(LOG_DIR / f"test_{timestamp}.log")

    # Add console handler if enabled
    if enable_console:
        console_handler = logging.StreamHandler(stream=sys.stdout)
        console_handler.setFormatter(fmt=_ColourFormatter(fmt=LOG_MESSAGE_FORMAT, datefmt=LOG_TIME_FORMAT))
        root_logger.addHandler(hdlr=console_handler)

    # Add file handler with proper error handling
    try:
        file_handler = RotatingFileHandler(
            filename=str(logfile_path),
            maxBytes=10_000_000,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt=plain_formatter)
        root_logger.addHandler(hdlr=file_handler)
    except (PermissionError, OSError) as e:
        # Clear any handlers that were added
        root_logger.handlers.clear()
        raise OSError(
            f"Cannot create log file at {logfile_path}. Ensure you have write permissions: {e}"
        )

    logging.captureWarnings(capture=True)
    logging.info(f"Logging configured - writing to: {logfile_path}")
