"""Statistics Panel Widget - Display performance statistics"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional

from loguru import logger


class StatisticsPanelWidget(tk.Frame):
    """Widget displaying chess performance statistics"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", **kwargs)

        # State
        self.stats_data = None

        # Monochromatic colors - only black, white, gray
        self.bg_color = "#1a1a1a"  # Dark gray background
        self.surface_color = "#2a2a2a"  # Slightly lighter surface
        self.accent_color = "#404040"  # Medium gray accent
        self.text_color = "#ffffff"  # Pure white text
        self.secondary_text = "#cccccc"  # Light gray text
        self.success_color = "#888888"  # Gray for success

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all statistics widgets"""
        self.title_label = tk.Label(
            self,
            text="Performance Statistics",
            font=("Arial", 14, "bold"),
            fg="#FFFFFF",
            bg="#2B2B2B",
        )

        # Overall stats frame - sleek card
        self.overall_frame = tk.Frame(self, bg=self.surface_color, relief="flat", borderwidth=1)

        self.overall_title = tk.Label(
            self.overall_frame,
            text="🏆 Overall Performance",
            font=("Segoe UI", 10, "bold"),
            fg=self.accent_color,
            bg=self.surface_color,
        )

        # Overall statistics labels with icons
        self.total_games_label = tk.Label(
            self.overall_frame,
            text="🎮 Total Games: 0",
            font=("Segoe UI", 9),
            fg=self.text_color,
            bg=self.surface_color,
        )

        self.win_rate_label = tk.Label(
            self.overall_frame,
            text="🏅 Win Rate: 0%",
            font=("Segoe UI", 9),
            fg=self.success_color,
            bg=self.surface_color,
        )

        self.avg_game_length_label = tk.Label(
            self.overall_frame,
            text="⏱ Avg Game Length: 0 moves",
            font=("Segoe UI", 9),
            fg=self.secondary_text,
            bg=self.surface_color,
        )

        self.avg_evaluation_label = tk.Label(
            self.overall_frame,
            text="📈 Avg Evaluation: N/A",
            font=("Segoe UI", 9),
            fg=self.text_color,
            bg=self.surface_color,
        )

        # Recent games frame
        self.recent_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.recent_title = tk.Label(
            self.recent_frame,
            text="Recent Games",
            font=("Arial", 12, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A",
        )

        # Treeview for recent games - compact for tabbed layout
        self.recent_tree = ttk.Treeview(
            self.recent_frame,
            columns=("result", "score", "moves", "date"),
            show="headings",
            height=5,  # More compact for tab
        )

        # Configure columns
        self.recent_tree.heading("result", text="Result")
        self.recent_tree.heading("score", text="Score")
        self.recent_tree.heading("moves", text="Moves")
        self.recent_tree.heading("date", text="Date")

        self.recent_tree.column("result", width=60, anchor="center")
        self.recent_tree.column("score", width=50, anchor="center")
        self.recent_tree.column("moves", width=50, anchor="center")
        self.recent_tree.column("date", width=100, anchor="center")

        # Configure treeview styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#1A1A1A",
            foreground="#CCCCCC",
            fieldbackground="#1A1A1A",
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#333333",
            foreground="#FFFFFF",
            borderwidth=1,
            relief="solid",
        )
        style.map("Treeview", background=[("selected", "#4A4A4A")])

        # Scrollbar for recent games
        self.recent_scrollbar = ttk.Scrollbar(
            self.recent_frame, orient="vertical", command=self.recent_tree.yview
        )
        self.recent_tree.configure(yscrollcommand=self.recent_scrollbar.set)

        # Export button
        self.export_button = tk.Button(
            self,
            text="Export PGN",
            font=("Arial", 9),
            bg="#4A4A4A",
            fg="#FFFFFF",
            activebackground="#666666",
            activeforeground="#FFFFFF",
            relief="raised",
            bd=1,
            command=self._export_pgn,
        )

        # Status label
        self.status_label = tk.Label(
            self,
            text="No statistics available",
            font=("Arial", 9),
            fg="#888888",
            bg="#2B2B2B",
        )

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Title
        self.title_label.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # Overall stats
        self.overall_frame.grid(row=1, column=0, pady=(0, 5), padx=5, sticky="ew")
        self.overall_frame.grid_columnconfigure(0, weight=1)

        self.overall_title.grid(row=0, column=0, pady=(5, 5), sticky="ew")
        self.total_games_label.grid(row=1, column=0, pady=1, padx=10, sticky="w")
        self.win_rate_label.grid(row=2, column=0, pady=1, padx=10, sticky="w")
        self.avg_game_length_label.grid(row=3, column=0, pady=1, padx=10, sticky="w")
        self.avg_evaluation_label.grid(row=4, column=0, pady=(1, 5), padx=10, sticky="w")

        # Recent games
        self.recent_frame.grid(row=2, column=0, pady=(0, 5), padx=5, sticky="nsew")
        self.recent_frame.grid_columnconfigure(0, weight=1)
        self.recent_frame.grid_rowconfigure(1, weight=1)

        self.recent_title.grid(row=0, column=0, pady=(5, 3), sticky="ew")

        # Tree and scrollbar
        self.recent_tree.grid(row=1, column=0, sticky="nsew", padx=(10, 0))
        self.recent_scrollbar.grid(row=1, column=1, sticky="ns", padx=(0, 10))

        # Export button
        self.export_button.grid(row=3, column=0, pady=(2, 3), padx=5, sticky="ew")

        # Status
        self.status_label.grid(row=4, column=0, pady=(0, 5), sticky="ew")

    def update_statistics(self, stats_data: Dict):
        """Update the statistics display"""
        try:
            self.stats_data = stats_data

            # Update overall statistics
            total_games = stats_data.get("total_games", 0)
            win_rate = stats_data.get("win_rate", 0)
            avg_length = stats_data.get("average_game_length", 0)
            avg_eval = stats_data.get("average_evaluation")

            self.total_games_label.configure(text=f"Total Games: {total_games}")
            self.win_rate_label.configure(text=f"Win Rate: {win_rate}%")

            if avg_length > 0:
                self.avg_game_length_label.configure(text=f"Avg Game Length: {avg_length:.1f} moves")
            else:
                self.avg_game_length_label.configure(text="Avg Game Length: N/A")

            if avg_eval is not None:
                self.avg_evaluation_label.configure(text=f"Avg Evaluation: {avg_eval:+.2f}")
            else:
                self.avg_evaluation_label.configure(text="Avg Evaluation: N/A")

            # Update recent games
            self._update_recent_games(stats_data.get("recent_games", []))

            # Update status
            if total_games > 0:
                self.status_label.configure(text=f"Statistics updated - {total_games} games total")
            else:
                self.status_label.configure(text="No games played yet")

        except Exception as e:
            logger.error(f"Failed to update statistics display: {e}")
            self.status_label.configure(text="Error loading statistics")

    def _update_recent_games(self, recent_games: List[Dict]):
        """Update the recent games treeview"""
        # Clear existing items
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        # Add recent games
        for game in recent_games[:10]:  # Show last 10 games
            try:
                result = game.get("result", "unknown")
                score = game.get("score", "N/A")
                moves = game.get("total_moves", 0)

                # Format date
                date_str = "N/A"
                if game.get("start_time"):
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(game["start_time"])
                        date_str = dt.strftime("%m/%d %H:%M")
                    except:
                        pass

                # Color code results
                result_display = result.upper()
                if result == "win":
                    result_display = "WIN"
                elif result == "loss":
                    result_display = "LOSS"
                elif result == "draw":
                    result_display = "DRAW"

                self.recent_tree.insert(
                    "",
                    "end",
                    values=(result_display, score, moves, date_str),
                )
            except Exception as e:
                logger.debug(f"Failed to add game to recent list: {e}")

    def get_statistics_data(self) -> Optional[Dict]:
        """Get the current statistics data"""
        return self.stats_data

    def _export_pgn(self):
        """Export games to PGN file"""
        if not self.stats_data or self.stats_data.get("total_games", 0) == 0:
            self.status_label.configure(text="No games to export", fg="#FF8888")
            return

        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".pgn",
                filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")],
                title="Export Games to PGN"
            )

            if filename:
                # Note: This would need access to the statistics manager
                # For now, just show a placeholder message
                self.status_label.configure(text=f"PGN export to {filename} not yet implemented", fg="#888888")
            else:
                self.status_label.configure(text="Export cancelled", fg="#888888")

        except Exception as e:
            self.status_label.configure(text=f"Export failed: {e}", fg="#FF8888")

    def clear_statistics(self):
        """Clear the statistics display"""
        self.update_statistics({
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_rate": 0,
            "average_game_length": 0,
            "average_evaluation": None,
            "recent_games": [],
        })
