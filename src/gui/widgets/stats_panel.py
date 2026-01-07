"""Statistics Panel Widget - Display performance statistics"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from ...utils.logging import logger


class StatisticsPanelWidget(tk.Frame):
    """Widget displaying chess performance statistics"""

    def __init__(self, parent, compact=False, **kwargs):
        super().__init__(parent, bg="#1a1a1a", **kwargs)
        self.compact = compact
        self.stats_data = None
        self.session_stats_data = None
        self.all_time_stats_data = None
        self.show_session = True  # Default to session view

        self.bg_color = "#1a1a1a"
        self.surface_color = "#2a2a2a"
        self.text_color = "#ffffff"
        self.secondary_text = "#888888"
        self.accent_color = "#7aa2f7"

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create statistics widgets"""
        font = ("Consolas", 9) if self.compact else ("Segoe UI", 10)
        btn_font = ("Consolas", 8) if self.compact else ("Segoe UI", 9)

        # Mode toggle frame
        self.toggle_frame = tk.Frame(self, bg=self.bg_color)

        self.session_btn = tk.Button(
            self.toggle_frame,
            text="Session",
            font=btn_font,
            fg=self.text_color,
            bg=self.accent_color,
            activebackground=self.accent_color,
            activeforeground=self.text_color,
            relief="flat",
            padx=8,
            pady=2,
            command=lambda: self._set_mode(True),
        )

        self.alltime_btn = tk.Button(
            self.toggle_frame,
            text="All Time",
            font=btn_font,
            fg=self.secondary_text,
            bg=self.surface_color,
            activebackground=self.surface_color,
            activeforeground=self.text_color,
            relief="flat",
            padx=8,
            pady=2,
            command=lambda: self._set_mode(False),
        )

        # Stats grid
        self.stats_frame = tk.Frame(self, bg=self.surface_color)

        self.total_label = tk.Label(
            self.stats_frame,
            text="Games: 0",
            font=font,
            fg=self.text_color,
            bg=self.surface_color,
        )

        self.wins_label = tk.Label(
            self.stats_frame,
            text="W: 0",
            font=font,
            fg="#a6e3a1",
            bg=self.surface_color,
        )

        self.losses_label = tk.Label(
            self.stats_frame,
            text="L: 0",
            font=font,
            fg="#f38ba8",
            bg=self.surface_color,
        )

        self.draws_label = tk.Label(
            self.stats_frame,
            text="D: 0",
            font=font,
            fg="#888888",
            bg=self.surface_color,
        )

        self.winrate_label = tk.Label(
            self.stats_frame,
            text="Rate: 0%",
            font=font,
            fg=self.text_color,
            bg=self.surface_color,
        )

        # Recent games list
        self.recent_frame = tk.Frame(self, bg=self.bg_color)

        style = ttk.Style()
        style.configure(
            "Compact.Treeview",
            background=self.bg_color,
            foreground=self.secondary_text,
            fieldbackground=self.bg_color,
            rowheight=18 if self.compact else 22,
        )
        style.configure(
            "Compact.Treeview.Heading",
            background="#333333",
            foreground="#ffffff",
            font=("Consolas", 8),
        )

        self.recent_tree = ttk.Treeview(
            self.recent_frame,
            columns=("result", "score", "moves"),
            show="headings",
            height=6 if self.compact else 8,
            style="Compact.Treeview",
        )

        self.recent_tree.heading("result", text="Result")
        self.recent_tree.heading("score", text="Score")
        self.recent_tree.heading("moves", text="Moves")

        self.recent_tree.column("result", width=50, anchor="center")
        self.recent_tree.column("score", width=50, anchor="center")
        self.recent_tree.column("moves", width=50, anchor="center")

        self.scrollbar = ttk.Scrollbar(
            self.recent_frame, orient="vertical", command=self.recent_tree.yview
        )
        self.recent_tree.configure(yscrollcommand=self.scrollbar.set)

    def _setup_layout(self):
        """Setup layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Toggle buttons
        self.toggle_frame.grid(row=0, column=0, sticky="w", padx=4, pady=(4, 0))
        self.session_btn.pack(side="left", padx=(0, 2))
        self.alltime_btn.pack(side="left")

        # Stats row
        self.stats_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.total_label.grid(row=0, column=0, padx=2, pady=4)
        self.wins_label.grid(row=0, column=1, padx=2, pady=4)
        self.losses_label.grid(row=0, column=2, padx=2, pady=4)
        self.draws_label.grid(row=0, column=3, padx=2, pady=4)
        self.winrate_label.grid(row=0, column=4, padx=2, pady=4)

        # Recent games
        self.recent_frame.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        self.recent_frame.grid_columnconfigure(0, weight=1)
        self.recent_frame.grid_rowconfigure(0, weight=1)

        self.recent_tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

    def _set_mode(self, session: bool):
        """Switch between session and all-time stats"""
        self.show_session = session

        # Update button styles
        if session:
            self.session_btn.configure(fg=self.text_color, bg=self.accent_color)
            self.alltime_btn.configure(fg=self.secondary_text, bg=self.surface_color)
        else:
            self.session_btn.configure(fg=self.secondary_text, bg=self.surface_color)
            self.alltime_btn.configure(fg=self.text_color, bg=self.accent_color)

        # Refresh display with appropriate data
        data = self.session_stats_data if session else self.all_time_stats_data
        if data:
            self._display_stats(data)

    def update_statistics(
        self, stats_data: Dict = None, session_data: Dict = None, all_time_data: Dict = None
    ):
        """Update statistics display with session and all-time data"""
        try:
            # Legacy single-data mode
            if stats_data and not session_data and not all_time_data:
                self.session_stats_data = stats_data
                self.all_time_stats_data = stats_data
            else:
                if session_data:
                    self.session_stats_data = session_data
                if all_time_data:
                    self.all_time_stats_data = all_time_data

            # Display current mode
            data = self.session_stats_data if self.show_session else self.all_time_stats_data
            if data:
                self._display_stats(data)

        except Exception as e:
            logger.error(f"Stats update error: {e}")

    def _display_stats(self, stats_data: Dict):
        """Display stats data in the UI"""
        self.stats_data = stats_data

        total = stats_data.get("total_games", 0)
        wins = stats_data.get("wins", 0)
        losses = stats_data.get("losses", 0)
        draws = stats_data.get("draws", 0)
        rate = stats_data.get("win_rate", 0)

        self.total_label.configure(text=f"Games: {total}")
        self.wins_label.configure(text=f"W: {wins}")
        self.losses_label.configure(text=f"L: {losses}")
        self.draws_label.configure(text=f"D: {draws}")
        self.winrate_label.configure(text=f"Rate: {rate}%")

        self._update_recent_games(stats_data.get("recent_games", []))

    def _update_recent_games(self, games: List[Dict]):
        """Update recent games list"""
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        for game in games[:10]:
            result = game.get("result", "?").upper()[:1]
            score = game.get("score", "?")
            moves = game.get("total_moves", 0)

            self.recent_tree.insert("", "end", values=(result, score, moves))

    def get_statistics_data(self) -> Optional[Dict]:
        """Get current stats data"""
        return self.stats_data

    def clear_statistics(self):
        """Clear display"""
        empty = {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_rate": 0,
            "recent_games": [],
        }
        self.update_statistics(session_data=empty, all_time_data=empty)
