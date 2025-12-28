"""Log Panel Widget - Real-time logging and status display"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Dict


class LogPanelWidget(tk.Frame):
    """Panel for displaying real-time logs and status messages"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", **kwargs)

        # Configuration
        self.max_lines = 300  # Reduced from 500 to reduce memory usage
        self.auto_scroll = True

        # Log level filtering
        self.visible_levels = {"info", "success", "warning", "error", "critical"}  # Hide debug by default

        # Rate limiting to prevent spam
        self.last_log_time = 0
        self.min_log_interval = 0.1  # Minimum 100ms between similar logs
        self.recent_messages = {}  # Track recent messages to prevent duplicates

        # Monochromatic colors - only black, white, gray
        self.bg_color = "#1a1a1a"  # Dark gray background
        self.surface_color = "#2a2a2a"  # Slightly lighter surface
        self.accent_color = "#404040"  # Medium gray accent
        self.text_color = "#ffffff"  # Pure white text
        self.secondary_text = "#cccccc"  # Light gray text

        # Modern log level colors
        self.level_colors: Dict[str, str] = {
            "trace": "#6c7086",
            "debug": "#6c7086",
            "info": self.text_color,
            "success": "#a6e3a1",
            "warning": "#f9e2af",
            "error": "#f38ba8",
            "critical": "#f38ba8",
        }

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all log panel widgets"""

        # Sleek header
        self.header_frame = tk.Frame(self, bg=self.surface_color)

        self.title_label = tk.Label(
            self.header_frame,
            text="📋 Activity Log",
            font=("Segoe UI", 9, "bold"),
            fg=self.secondary_text,
            bg=self.surface_color,
        )

        self.clear_button = tk.Button(
            self.header_frame,
            text="🗑",
            command=self._clear_logs,
            font=("Segoe UI", 8),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.accent_color,
            activeforeground=self.text_color,
            relief="flat",
            borderwidth=0,
            padx=6,
            pady=2,
        )

        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_checkbox = tk.Checkbutton(
            self.header_frame,
            text="🔄 Auto",
            variable=self.auto_scroll_var,
            command=self._toggle_auto_scroll,
            font=("Segoe UI", 7),
            fg=self.secondary_text,
            bg=self.surface_color,
            selectcolor=self.accent_color,
            activebackground=self.surface_color,
            activeforeground=self.text_color,
        )

        # Log level filter checkbox
        self.show_debug_var = tk.BooleanVar(value=False)
        self.debug_checkbox = tk.Checkbutton(
            self.header_frame,
            text="🐛 Debug",
            variable=self.show_debug_var,
            command=self._toggle_debug_logs,
            font=("Segoe UI", 7),
            fg=self.secondary_text,
            bg=self.surface_color,
            selectcolor=self.accent_color,
            activebackground=self.surface_color,
            activeforeground=self.text_color,
        )

        # Sleek log display area
        self.log_frame = tk.Frame(self, bg=self.surface_color, relief="flat", borderwidth=1)

        # Text widget with sleek styling - larger font for readability
        self.log_text = tk.Text(
            self.log_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.surface_color,
            fg=self.text_color,
            insertbackground=self.text_color,
            selectbackground=self.accent_color,
            font=("JetBrains Mono", 9),  # Larger monospace font for better readability
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=4,
        )

        self.scrollbar = tk.Scrollbar(
            self.log_frame,
            command=self.log_text.yview,
            bg=self.surface_color,
            troughcolor=self.bg_color,
            borderwidth=0,
        )

        self.log_text.configure(yscrollcommand=self.scrollbar.set)

        # Configure text tags for different log levels
        for level, color in self.level_colors.items():
            self.log_text.tag_configure(level, foreground=color)

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Compact header
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(2, 2))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.debug_checkbox.grid(row=0, column=1, sticky="e", padx=(0, 5))
        self.auto_scroll_checkbox.grid(row=0, column=2, sticky="e", padx=(0, 5))
        self.clear_button.grid(row=0, column=3, sticky="e")

        # Compact log area
        self.log_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 2))
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
