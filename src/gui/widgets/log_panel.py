"""Log Panel Widget - Real-time logging and status display"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Dict


class LogPanelWidget(tk.Frame):
    """Panel for displaying real-time logs and status messages"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # Configuration
        self.max_lines = 300  # Reduced from 500 to reduce memory usage
        self.auto_scroll = True

        # Log level filtering
        self.visible_levels = {"info", "success", "warning", "error", "critical"}  # Hide debug by default

        # Rate limiting to prevent spam
        self.last_log_time = 0
        self.min_log_interval = 0.1  # Minimum 100ms between similar logs
        self.recent_messages = {}  # Track recent messages to prevent duplicates

        # Colors for different log levels
        self.level_colors: Dict[str, str] = {
            "trace": "#666666",
            "debug": "#666666",
            "info": "#FFFFFF",
            "success": "#28A745",
            "warning": "#FFC107",
            "error": "#DC3545",
            "critical": "#DC3545",
        }

        self._create_widgets()
        self._setup_layout()

        # Add minimal welcome message
        self.add_log("Ready", "success")

    def _create_widgets(self):
        """Create all log panel widgets"""

        # Title with controls
        self.header_frame = tk.Frame(self, bg="#2B2B2B")

        self.title_label = tk.Label(
            self.header_frame,
            text="Activity Log",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#2B2B2B",
        )

        self.clear_button = tk.Button(
            self.header_frame,
            text="Clear",
            command=self._clear_logs,
            font=("Arial", 9),
            bg="#404040",
            fg="#FFFFFF",
            relief="flat",
            bd=1,
            padx=10,
            pady=2,
        )

        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_checkbox = tk.Checkbutton(
            self.header_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#2B2B2B",
            selectcolor="#404040",
        )

        # Log level filter checkbox
        self.show_debug_var = tk.BooleanVar(value=False)
        self.debug_checkbox = tk.Checkbutton(
            self.header_frame,
            text="Debug",
            variable=self.show_debug_var,
            command=self._toggle_debug_logs,
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#2B2B2B",
            selectcolor="#404040",
        )

        # Log display area
        self.log_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        # Text widget with scrollbar
        self.log_text = tk.Text(
            self.log_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg="#1A1A1A",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            selectbackground="#404040",
            font=("Consolas", 9),
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=5,
        )

        self.scrollbar = tk.Scrollbar(
            self.log_frame,
            command=self.log_text.yview,
            bg="#404040",
            troughcolor="#2B2B2B",
        )

        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        # Configure text tags for different log levels
        for level, color in self.level_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label.grid(row=0, column=0, sticky="w")
        self.debug_checkbox.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.auto_scroll_checkbox.grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.clear_button.grid(row=0, column=3, sticky="e")

        # Log area
        self.log_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)

        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def add_log(self, message: str, level: str = "info"):
        """Add a log message with timestamp and level"""
        level = level.lower()

        # Filter out messages based on visibility settings
        if level not in self.visible_levels:
            return

        # Rate limiting and duplicate prevention
        current_time = datetime.now().timestamp()
        message_key = f"{level}:{message}"

        # Prevent exact duplicates within 2 seconds
        if message_key in self.recent_messages:
            if current_time - self.recent_messages[message_key] < 2.0:
                return

        # Rate limiting - minimum interval between any logs
        if current_time - self.last_log_time < self.min_log_interval:
            return

        self.recent_messages[message_key] = current_time
        self.last_log_time = current_time

        # Clean up old entries from recent_messages (keep last 50)
        if len(self.recent_messages) > 50:
            oldest_key = min(self.recent_messages.keys(), key=lambda k: self.recent_messages[k])
            del self.recent_messages[oldest_key]

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format the log entry
        log_entry = f"[{timestamp}] {message}\n"

        # Insert the log entry
        self.log_text.configure(state=tk.NORMAL)

        # Insert with appropriate color
        if level in self.level_colors:
            self.log_text.insert(tk.END, log_entry, level)
        else:
            self.log_text.insert(tk.END, log_entry, "info")

        # Manage line count
        self._manage_line_count()

        self.log_text.configure(state=tk.DISABLED)

        # Auto-scroll if enabled
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def _manage_line_count(self):
        """Keep log text under the maximum line limit"""
        lines = self.log_text.get("1.0", tk.END).count("\n")
        if lines > self.max_lines:
            # Remove oldest lines
            lines_to_remove = lines - self.max_lines
            self.log_text.delete("1.0", f"{lines_to_remove + 1}.0")

    def _clear_logs(self):
        """Clear all log messages"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.add_log("Log cleared", "info")

    def _toggle_auto_scroll(self):
        """Toggle auto-scroll functionality"""
        self.auto_scroll = self.auto_scroll_var.get()
        if self.auto_scroll:
            self.log_text.see(tk.END)

    def _toggle_debug_logs(self):
        """Toggle debug log visibility"""
        if self.show_debug_var.get():
            self.visible_levels.add("debug")
            self.visible_levels.add("trace")
        else:
            self.visible_levels.discard("debug")
            self.visible_levels.discard("trace")

    def bulk_add_logs(self, logs: list):
        """Add multiple log entries at once (more efficient)"""
        if not logs:
            return

        self.log_text.configure(state=tk.NORMAL)

        for log_data in logs:
            if isinstance(log_data, dict):
                message = log_data.get("message", "")
                level = log_data.get("level", "info")
            else:
                message = str(log_data)
                level = "info"

            level = level.lower()

            # Filter out messages based on visibility settings
            if level not in self.visible_levels:
                continue

            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"

            if level in self.level_colors:
                self.log_text.insert(tk.END, log_entry, level)
            else:
                self.log_text.insert(tk.END, log_entry, "info")

        self._manage_line_count()
        self.log_text.configure(state=tk.DISABLED)

        if self.auto_scroll:
            self.log_text.see(tk.END)
