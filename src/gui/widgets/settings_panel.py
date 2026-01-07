"""Settings Panel Widget - In-app configuration editor"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from ...utils.logging import logger
from ...config.presets import get_all_presets, apply_preset


class SettingsPanelWidget(tk.Frame):
    """Widget for editing bot settings in real-time"""

    def __init__(self, parent, config_manager, on_save: Optional[Callable] = None, **kwargs):
        super().__init__(parent, bg="#1a1a1a", **kwargs)

        self.config = config_manager
        self.on_save = on_save
        self.vars = {}

        self._create_scrollable_container()
        self._create_widgets()
        self._load_current_values()

    def _create_scrollable_container(self):
        """Create scrollable container for settings"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Canvas for scrolling
        self.canvas = tk.Canvas(self, bg="#1a1a1a", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#1a1a1a")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind canvas resize to adjust inner frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def _on_canvas_configure(self, event):
        """Adjust scrollable frame width to match canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _create_widgets(self):
        """Create settings widgets"""
        container = self.scrollable_frame
        container.grid_columnconfigure(0, weight=1)

        label_style = {"font": ("Segoe UI", 9), "fg": "#cccccc", "bg": "#1a1a1a"}
        entry_style = {
            "font": ("Consolas", 9), "bg": "#2a2a2a", "fg": "#ffffff",
            "insertbackground": "#ffffff", "relief": "flat", "width": 6
        }

        row = 0

        # Title
        tk.Label(
            container, text="Settings", font=("Segoe UI", 11, "bold"),
            fg="#ffffff", bg="#1a1a1a"
        ).grid(row=row, column=0, pady=(0, 8), sticky="w")
        row += 1

        # Presets section
        presets_frame = tk.LabelFrame(
            container, text="Presets", font=("Segoe UI", 9),
            fg="#888888", bg="#1a1a1a", relief="flat"
        )
        presets_frame.grid(row=row, column=0, sticky="ew", pady=4)
        presets_frame.grid_columnconfigure((0, 1), weight=1)
        row += 1

        preset_btn_style = {
            "font": ("Segoe UI", 8, "bold"),
            "fg": "#ffffff",
            "relief": "flat",
            "cursor": "hand2",
        }

        # 2x2 grid for presets
        tk.Button(
            presets_frame, text="Bullet", bg="#cc4444",
            activebackground="#dd5555",
            command=lambda: self._apply_preset("bullet"), **preset_btn_style
        ).grid(row=0, column=0, padx=2, pady=2, sticky="ew")

        tk.Button(
            presets_frame, text="Blitz", bg="#cc8844",
            activebackground="#dd9955",
            command=lambda: self._apply_preset("blitz"), **preset_btn_style
        ).grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        tk.Button(
            presets_frame, text="Rapid", bg="#4488cc",
            activebackground="#5599dd",
            command=lambda: self._apply_preset("rapid"), **preset_btn_style
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")

        tk.Button(
            presets_frame, text="Classical", bg="#448844",
            activebackground="#559955",
            command=lambda: self._apply_preset("classical"), **preset_btn_style
        ).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        # Engine section
        engine_frame = tk.LabelFrame(
            container, text="Engine", font=("Segoe UI", 9),
            fg="#888888", bg="#1a1a1a", relief="flat"
        )
        engine_frame.grid(row=row, column=0, sticky="ew", pady=4)
        engine_frame.grid_columnconfigure(1, weight=1)
        row += 1

        tk.Label(engine_frame, text="Depth:", **label_style).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["depth"] = tk.StringVar()
        tk.Entry(engine_frame, textvariable=self.vars["depth"], **entry_style).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        tk.Label(engine_frame, text="Skill:", **label_style).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.vars["skill"] = tk.StringVar()
        tk.Entry(engine_frame, textvariable=self.vars["skill"], **entry_style).grid(row=1, column=1, sticky="w", padx=5, pady=2)

        # General section
        general_frame = tk.LabelFrame(
            container, text="General", font=("Segoe UI", 9),
            fg="#888888", bg="#1a1a1a", relief="flat"
        )
        general_frame.grid(row=row, column=0, sticky="ew", pady=4)
        row += 1

        self.vars["arrow"] = tk.BooleanVar()
        tk.Checkbutton(
            general_frame, text="Show arrow", variable=self.vars["arrow"],
            font=("Segoe UI", 9), fg="#cccccc", bg="#1a1a1a",
            selectcolor="#2a2a2a", activebackground="#1a1a1a", activeforeground="#ffffff"
        ).grid(row=0, column=0, sticky="w", padx=5, pady=2)

        self.vars["auto_preset"] = tk.BooleanVar()
        tk.Checkbutton(
            general_frame, text="Auto-preset", variable=self.vars["auto_preset"],
            font=("Segoe UI", 9), fg="#cccccc", bg="#1a1a1a",
            selectcolor="#2a2a2a", activebackground="#1a1a1a", activeforeground="#ffffff"
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)

        # Delays section
        delays_frame = tk.LabelFrame(
            container, text="Delays (sec)", font=("Segoe UI", 9),
            fg="#888888", bg="#1a1a1a", relief="flat"
        )
        delays_frame.grid(row=row, column=0, sticky="ew", pady=4)
        delays_frame.grid_columnconfigure((1, 3), weight=1)
        row += 1

        tk.Label(delays_frame, text="Min:", **label_style).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["min_delay"] = tk.StringVar()
        tk.Entry(delays_frame, textvariable=self.vars["min_delay"], **entry_style).grid(row=0, column=1, sticky="w", padx=2, pady=2)

        tk.Label(delays_frame, text="Max:", **label_style).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.vars["max_delay"] = tk.StringVar()
        tk.Entry(delays_frame, textvariable=self.vars["max_delay"], **entry_style).grid(row=0, column=3, sticky="w", padx=2, pady=2)

        # Save button - at bottom
        self.save_btn = tk.Button(
            container, text="Save & Apply", font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg="#3a8a3a", activebackground="#4a9a4a",
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            command=self._save_settings
        )
        self.save_btn.grid(row=row, column=0, sticky="ew", pady=(12, 4))
        row += 1

        # Status label
        self.status_label = tk.Label(
            container, text="", font=("Segoe UI", 8),
            fg="#888888", bg="#1a1a1a"
        )
        self.status_label.grid(row=row, column=0, sticky="ew")

    def _load_current_values(self):
        """Load current config values into UI"""
        try:
            self.vars["depth"].set(self.config.get("engine", "depth", "5"))
            self.vars["skill"].set(self.config.get("engine", "skill-level", "14"))
            self.vars["arrow"].set(self.config.show_arrow)
            self.vars["auto_preset"].set(self.config.is_auto_preset_enabled)
            self.vars["min_delay"].set(self.config.get("humanization", "min-delay", "0.3"))
            self.vars["max_delay"].set(self.config.get("humanization", "max-delay", "1.8"))
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def _save_settings(self):
        """Save settings to config"""
        try:
            depth = int(self.vars["depth"].get())
            skill = int(self.vars["skill"].get())
            min_delay = float(self.vars["min_delay"].get())
            max_delay = float(self.vars["max_delay"].get())

            if depth < 1 or depth > 30:
                raise ValueError("Depth must be 1-30")
            if skill < 0 or skill > 20:
                raise ValueError("Skill must be 0-20")
            if min_delay < 0 or max_delay < min_delay:
                raise ValueError("Invalid delay values")

            self.config.set("engine", "depth", str(depth))
            self.config.set("engine", "skill-level", str(skill))
            self.config.set("general", "arrow", str(self.vars["arrow"].get()).lower())
            self.config.set("general", "auto-preset", str(self.vars["auto_preset"].get()).lower())
            self.config.set("humanization", "min-delay", str(min_delay))
            self.config.set("humanization", "max-delay", str(max_delay))

            self.config.save()
            self._flash_status("Saved!", "#66ff66")

            if self.on_save:
                self.on_save()

        except ValueError as e:
            self._flash_status(str(e), "#ff6666")
        except Exception as e:
            self._flash_status("Error", "#ff6666")
            logger.error(f"Failed to save settings: {e}")

    def _flash_status(self, text: str, color: str):
        """Show temporary status message"""
        self.status_label.configure(text=text, fg=color)
        self.after(3000, lambda: self.status_label.configure(text=""))

    def _apply_preset(self, preset_name: str):
        """Apply a preset and reload values"""
        try:
            if apply_preset(self.config, preset_name):
                self._load_current_values()
                presets = get_all_presets()
                preset = presets.get(preset_name)
                self._flash_status(f"{preset.name} applied!", "#66ff66")
            else:
                self._flash_status("Unknown preset", "#ff6666")
        except Exception as e:
            self._flash_status("Failed to apply", "#ff6666")
            logger.error(f"Failed to apply preset: {e}")
