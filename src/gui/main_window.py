"""Compact GUI Window for Chess Bot"""

import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional

import chess
from loguru import logger

from .widgets.chess_board import ChessBoardWidget
from .widgets.log_panel import LogPanelWidget
from .widgets.move_history import MoveHistoryWidget
from .widgets.result_popup import show_game_result
from .widgets.stats_panel import StatisticsPanelWidget


class ChessBotGUI:
    """Compact overlay-style GUI for the chess bot"""

    def __init__(self, game_manager=None):
        self.game_manager = game_manager
        self._create_main_window()
        self._setup_layout()
        self._setup_callbacks()

        self.current_board = chess.Board()
        self.our_color = "white"
        self.current_suggestion = None
        self.is_running = False

    def _create_main_window(self):
        """Create compact main window"""
        self.root = tk.Tk()
        self.root.title("Chess Bot")
        self.root.geometry("320x480")
        self.root.minsize(280, 400)
        self.root.maxsize(400, 600)
        self.root.configure(bg="#1a1a1a")
        self.root.attributes("-topmost", True)  # Always on top

        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

    def _setup_layout(self):
        """Setup compact layout"""
        # Header with status
        header = tk.Frame(self.root, bg="#252525", height=50)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header.grid_columnconfigure(1, weight=1)

        # Mode indicator
        self.mode_label = tk.Label(
            header,
            text="⚡ AUTO",
            font=("Consolas", 10, "bold"),
            fg="#00DD88",
            bg="#252525",
        )
        self.mode_label.grid(row=0, column=0, padx=(10, 8), pady=8)

        # Current suggestion
        self.suggestion_label = tk.Label(
            header,
            text="--",
            font=("Consolas", 14, "bold"),
            fg="#ffffff",
            bg="#252525",
        )
        self.suggestion_label.grid(row=0, column=1, pady=8)

        # Game status
        self.status_label = tk.Label(
            header,
            text="●",
            font=("Consolas", 12),
            fg="#888888",
            bg="#252525",
        )
        self.status_label.grid(row=0, column=2, padx=(8, 10), pady=8)

        # Notebook for tabs
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1a1a1a", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background="#2a2a2a",
            foreground="#888888",
            padding=[12, 4],
            font=("Segoe UI", 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#333333")],
            foreground=[("selected", "#ffffff")],
        )

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)

        # Board tab (first)
        board_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        board_frame.grid_columnconfigure(0, weight=1)
        board_frame.grid_rowconfigure(0, weight=1)
        self.chess_board = ChessBoardWidget(board_frame)
        self.chess_board.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(board_frame, text="Board")

        # Log tab
        log_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        self.log_panel = LogPanelWidget(log_frame, compact=True)
        self.log_panel.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(log_frame, text="Log")

        # Moves tab
        moves_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        moves_frame.grid_columnconfigure(0, weight=1)
        moves_frame.grid_rowconfigure(0, weight=1)
        self.move_history = MoveHistoryWidget(moves_frame)
        self.move_history.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(moves_frame, text="Moves")

        # Stats tab
        stats_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)
        self.stats_panel = StatisticsPanelWidget(stats_frame, compact=True)
        self.stats_panel.grid(row=0, column=0, sticky="nsew")
        self.notebook.add(stats_frame, text="Stats")

        # Footer
        footer = tk.Frame(self.root, bg="#1a1a1a", height=24)
        footer.grid(row=2, column=0, sticky="ew", padx=8, pady=(4, 8))

        self.footer_label = tk.Label(
            footer,
            text="Waiting for game...",
            font=("Segoe UI", 8),
            fg="#666666",
            bg="#1a1a1a",
        )
        self.footer_label.pack(side=tk.LEFT)

        self._update_initial_status()

    def _update_initial_status(self):
        """Update initial status"""
        if not self.game_manager:
            return

        cfg = self.game_manager.config_manager
        if cfg.is_autoplay_enabled:
            self.mode_label.configure(text="⚡ AUTO", fg="#00DD88")
        else:
            self.mode_label.configure(text=f"⌨ {cfg.move_key.upper()}", fg="#FFB347")

    def _setup_callbacks(self):
        """Setup callbacks"""
        if self.game_manager:
            self.game_manager.set_gui_callback(self.update_from_game_manager)

        self.root.after(1000, self._auto_start_bot)

    def _auto_start_bot(self):
        """Auto-start the bot"""
        if not self.is_running and self.game_manager:
            self.is_running = True
            self.log_panel.add_log("Starting bot...", "info")
            threading.Thread(target=self._run_game_manager, daemon=True).start()

    def _run_game_manager(self):
        """Run game manager in thread"""
        try:
            if self.game_manager:
                self.game_manager.start()
        except Exception as e:
            self.log_panel.add_log(f"Error: {e}", "error")
            self.is_running = False

    def update_from_game_manager(self, update_data: dict):
        """Handle game manager updates"""
        try:
            t = update_data.get("type")

            if t == "board_update":
                board = update_data.get("board")
                last_move = update_data.get("last_move")
                if board:
                    self.current_board = board.copy()
                    self.chess_board.update_position(board, last_move)
                    if last_move:
                        self.chess_board.clear_suggestion()
                        self.current_suggestion = None

            elif t == "suggestion":
                move = update_data.get("move")
                if move:
                    self.suggestion_label.configure(text=str(move).upper())
                    self.current_suggestion = move
                    self.chess_board.show_suggestion(move)

            elif t == "game_info":
                if update_data.get("game_active"):
                    self.status_label.configure(fg="#00DD88")
                    color = update_data.get("our_color", "")
                    self.footer_label.configure(text=f"Playing as {color}")
                    if color:
                        self.our_color = color
                        self.chess_board.set_orientation(color)
                else:
                    self.status_label.configure(fg="#888888")

            elif t == "move_played":
                self.add_move_to_history(
                    update_data.get("move"),
                    update_data.get("move_number"),
                    update_data.get("is_white"),
                )
                self.suggestion_label.configure(text="--")

            elif t == "game_start":
                self.move_history.clear_history()
                self.suggestion_label.configure(text="--")

            elif t == "game_finished":
                self.show_game_result(update_data)

            elif t == "statistics_update":
                self.stats_panel.update_statistics(update_data.get("stats", {}))

        except Exception as e:
            logger.error(f"GUI update error: {e}")

    def add_log(self, message: str, level: str = "info"):
        """Add log message"""
        self.log_panel.add_log(message, level)

    def add_move_to_history(self, move: chess.Move, move_number: int, is_white: bool):
        """Add move to history"""
        if move:
            self.move_history.add_move(move, move_number, is_white)

    def show_game_result(self, result_data: dict):
        """Show game result"""
        try:
            show_game_result(result_data)
            if self.game_manager:
                self.game_manager.acknowledge_game_result()
        except Exception as e:
            logger.error(f"Result popup error: {e}")
            self.add_log(f"Game: {result_data.get('score', '?')}", "success")
            if self.game_manager:
                self.game_manager.acknowledge_game_result()

    def run(self):
        """Start GUI"""
        self.root.mainloop()

    def destroy(self):
        """Cleanup"""
        if self.root:
            self.root.destroy()
