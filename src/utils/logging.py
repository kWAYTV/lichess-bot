"""Logging utilities - Standard library logging setup"""

import logging
import sys
from typing import Optional

# Global logger instance
logger = logging.getLogger("helping-hand")


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
                text = self.format(record)
                self.gui.root.after(0, lambda: self.gui.add_log(text, level))
        except Exception:
            pass


def setup_logging(level: str = "INFO", gui_handler: Optional[GUILogHandler] = None) -> None:
    """Configure logging with optional GUI handler"""
    # Clear existing handlers
    logger.handlers.clear()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(getattr(logging, level.upper(), logging.INFO))
    console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", "%H:%M:%S"))
    logger.addHandler(console)

    # GUI handler
    if gui_handler:
        gui_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        gui_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(gui_handler)
