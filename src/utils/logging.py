"""Logging utilities"""


class GUILogHandler:
    """Custom log handler that forwards logs to GUI"""

    def __init__(self):
        self.gui = None

    def set_gui(self, gui):
        """Set the GUI instance for log forwarding"""
        self.gui = gui

    def write(self, message):
        """Forward log messages to GUI"""
        try:
            if self.gui and hasattr(message, "record"):
                level = message.record["level"].name.lower()
                text = message.record["message"]

                if hasattr(self.gui, "root") and self.gui.root:
                    self.gui.root.after(0, lambda: self.gui.add_log(text, level))
        except Exception:
            pass

        return ""

    def flush(self):
        """Required for file-like objects"""
        pass

