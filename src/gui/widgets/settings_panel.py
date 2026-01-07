"""Settings Panel Widget - In-app configuration editor"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from loguru import logger


class SettingsPanelWidget(tk.Frame):
    """Widget for editing bot settings in real-time"""

    def __init__(self, parent, config_manager, on_save: Optional[Callable] = None, **kwargs):
        super().__init__(parent, bg="#1a1a1a", **kwargs)
        
        self.config = config_manager
        self.on_save = on_save
        self.vars = {}  # Store tkinter variables
        
        self._create_widgets()
        self._setup_layout()
        self._load_current_values()

    def _create_widgets(self):
        """Create settings widgets"""
        # Style
        self.label_style = {"font": ("Segoe UI", 9), "fg": "#cccccc", "bg": "#1a1a1a"}
        self.entry_style = {"font": ("Consolas", 9), "bg": "#2a2a2a", "fg": "#ffffff", 
                           "insertbackground": "#ffffff", "relief": "flat", "width": 8}
        
        # Title
        self.title = tk.Label(self, text="⚙️ Settings", font=("Segoe UI", 11, "bold"),
                              fg="#ffffff", bg="#1a1a1a")
        
        # Engine section
        self.engine_frame = tk.LabelFrame(self, text="Engine", font=("Segoe UI", 9),
                                          fg="#888888", bg="#1a1a1a", relief="flat")
        
        # Depth
        tk.Label(self.engine_frame, text="Depth:", **self.label_style).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["depth"] = tk.StringVar()
        self.depth_entry = tk.Entry(self.engine_frame, textvariable=self.vars["depth"], **self.entry_style)
        self.depth_entry.grid(row=0, column=1, padx=5, pady=2)
        
        # Skill Level
        tk.Label(self.engine_frame, text="Skill:", **self.label_style).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.vars["skill"] = tk.StringVar()
        self.skill_entry = tk.Entry(self.engine_frame, textvariable=self.vars["skill"], **self.entry_style)
        self.skill_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # General section
        self.general_frame = tk.LabelFrame(self, text="General", font=("Segoe UI", 9),
                                           fg="#888888", bg="#1a1a1a", relief="flat")
        
        # Auto-play toggle
        self.vars["autoplay"] = tk.BooleanVar()
        self.autoplay_check = tk.Checkbutton(
            self.general_frame, text="Auto-play", variable=self.vars["autoplay"],
            font=("Segoe UI", 9), fg="#cccccc", bg="#1a1a1a",
            selectcolor="#2a2a2a", activebackground="#1a1a1a", activeforeground="#ffffff"
        )
        self.autoplay_check.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        
        # Show arrow toggle
        self.vars["arrow"] = tk.BooleanVar()
        self.arrow_check = tk.Checkbutton(
            self.general_frame, text="Show arrow", variable=self.vars["arrow"],
            font=("Segoe UI", 9), fg="#cccccc", bg="#1a1a1a",
            selectcolor="#2a2a2a", activebackground="#1a1a1a", activeforeground="#ffffff"
        )
        self.arrow_check.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        # Humanization section
        self.human_frame = tk.LabelFrame(self, text="Delays (seconds)", font=("Segoe UI", 9),
                                         fg="#888888", bg="#1a1a1a", relief="flat")
        
        # Min delay
        tk.Label(self.human_frame, text="Min:", **self.label_style).grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.vars["min_delay"] = tk.StringVar()
        tk.Entry(self.human_frame, textvariable=self.vars["min_delay"], **self.entry_style).grid(row=0, column=1, padx=5, pady=2)
        
        # Max delay
        tk.Label(self.human_frame, text="Max:", **self.label_style).grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.vars["max_delay"] = tk.StringVar()
        tk.Entry(self.human_frame, textvariable=self.vars["max_delay"], **self.entry_style).grid(row=0, column=3, padx=5, pady=2)
        
        # Save button
        self.save_btn = tk.Button(
            self, text="💾 Save & Apply", font=("Segoe UI", 9, "bold"),
            fg="#ffffff", bg="#3a8a3a", activebackground="#4a9a4a",
            activeforeground="#ffffff", relief="flat", cursor="hand2",
            command=self._save_settings
        )
        
        # Status label
        self.status_label = tk.Label(self, text="", font=("Segoe UI", 8),
                                     fg="#888888", bg="#1a1a1a")

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        
        self.title.grid(row=0, column=0, pady=(0, 8), sticky="w")
        self.engine_frame.grid(row=1, column=0, sticky="ew", pady=4)
        self.general_frame.grid(row=2, column=0, sticky="ew", pady=4)
        self.human_frame.grid(row=3, column=0, sticky="ew", pady=4)
        self.save_btn.grid(row=4, column=0, sticky="ew", pady=(8, 4))
        self.status_label.grid(row=5, column=0, sticky="ew")

    def _load_current_values(self):
        """Load current config values into UI"""
        try:
            # Engine
            self.vars["depth"].set(self.config.get("engine", "depth", "5"))
            self.vars["skill"].set(self.config.get("engine", "skill-level", "14"))
            
            # General
            self.vars["autoplay"].set(self.config.is_autoplay_enabled)
            self.vars["arrow"].set(self.config.show_arrow)
            
            # Humanization
            self.vars["min_delay"].set(self.config.get("humanization", "min-delay", "0.3"))
            self.vars["max_delay"].set(self.config.get("humanization", "max-delay", "1.8"))
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")

    def _save_settings(self):
        """Save settings to config"""
        try:
            # Validate
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
            
            # Apply
            self.config.set("engine", "depth", str(depth))
            self.config.set("engine", "skill-level", str(skill))
            self.config.set("general", "auto-play", str(self.vars["autoplay"].get()).lower())
            self.config.set("general", "arrow", str(self.vars["arrow"].get()).lower())
            self.config.set("humanization", "min-delay", str(min_delay))
            self.config.set("humanization", "max-delay", str(max_delay))
            
            self.config.save()
            
            self._flash_status("✓ Saved!", "#66ff66")
            logger.info("Settings saved")
            
            if self.on_save:
                self.on_save()
                
        except ValueError as e:
            self._flash_status(f"✗ {e}", "#ff6666")
        except Exception as e:
            self._flash_status(f"✗ Error", "#ff6666")
            logger.error(f"Failed to save settings: {e}")

    def _flash_status(self, text: str, color: str):
        """Show temporary status message"""
        self.status_label.configure(text=text, fg=color)
        self.after(3000, lambda: self.status_label.configure(text=""))

