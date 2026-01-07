"""Logging utilities - Structlog setup with runtime level control"""

import logging
import re
import sys
from typing import Optional

import structlog

# Root logger name
LOGGER_NAME = "helping-hand"

# Get stdlib logger for level control
_stdlib_logger = logging.getLogger(LOGGER_NAME)

# Regex to strip ANSI escape codes
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text"""
    return ANSI_ESCAPE.sub("", text)


class GUILogHandler(logging.Handler):
    """Custom log handler that forwards logs to GUI"""

    def __init__(self):
        super().__init__()
        self.gui = None

    def set_gui(self, gui):
        """Set the GUI instance for log forwarding"""
        self.gui = gui

    def emit(self, record: logging.LogRecord):
        """Forward log messages to GUI"""
        try:
            if self.gui and hasattr(self.gui, "root") and self.gui.root:
                level = record.levelname.lower()
                # Get the original message args, not the formatted structlog output
                # record.msg contains the event, record.args is empty for structlog
                # For structlog, the actual message is in the "event" key
                if hasattr(record, "_event_dict") and "event" in record._event_dict:
                    text = record._event_dict["event"]
                else:
                    # Fallback: parse from formatted message
                    text = strip_ansi(record.getMessage())
                    match = re.search(r"\]\s+(.+?)\s+\[[^\]]+\]$", text)
                    if match:
                        text = match.group(1).strip()
                self.gui.root.after(0, lambda: self.gui.add_log(text, level))
        except Exception:
            pass


def setup_logging(level: str = "INFO", gui_handler: Optional[GUILogHandler] = None) -> None:
    """Configure structlog with stdlib backend for runtime level control"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Clear existing handlers
    _stdlib_logger.handlers.clear()
    _stdlib_logger.setLevel(log_level)
    _stdlib_logger.propagate = False

    # Console handler with nice formatting
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(log_level)
    _stdlib_logger.addHandler(console)

    # GUI handler
    if gui_handler:
        gui_handler.setLevel(log_level)
        _stdlib_logger.addHandler(gui_handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(colors=True, pad_level=True),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,
    )


def set_level(level: str) -> None:
    """Change log level at runtime"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    _stdlib_logger.setLevel(log_level)
    for handler in _stdlib_logger.handlers:
        handler.setLevel(log_level)


def get_level() -> str:
    """Get current log level name"""
    return logging.getLevelName(_stdlib_logger.level)


# Global logger instance
logger = structlog.get_logger(LOGGER_NAME)
