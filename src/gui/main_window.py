"""Main GUI Window for Chess Bot"""

import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional

import chess
from loguru import logger

from .widgets.chess_board import ChessBoardWidget
from .widgets.game_info import GameInfoWidget
from .widgets.log_panel import LogPanelWidget
from .widgets.move_history import MoveHistoryWidget
from .widgets.result_popup import GameResultPopup, show_game_result
from .widgets.stats_panel import StatisticsPanelWidget


class ChessBotGUI:
    """Main GUI application for the chess bot"""

    def __init__(self, game_manager=None):
        self.game_manager = game_manager
        self._create_main_window()
        self._setup_layout()
        self._setup_callbacks()

        # State tracking
        self.current_board = chess.Board()
        self.our_color = "white"
        self.current_suggestion = None
        self.is_running = False

    def _create_main_window(self):
        """Create and configure the main window"""
        self.root = tk.Tk()
        self.root.title("Lichess Chess Bot")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        self.root.configure(bg="#1a1a1a")

        # Set window icon if available
        try:
            self.root.iconbitmap("assets/icon.ico")
        except:
            pass

        # Configure main grid - spacious three-section layout
        self.root.grid_columnconfigure(0, weight=4)  # Large chess board section
        self.root.grid_columnconfigure(1, weight=3)  # Tabbed info panels
        self.root.grid_rowconfigure(0, weight=1)     # Main content area
        self.root.grid_rowconfigure(1, weight=0)     # Bottom info bar (fixed height)

    def _setup_layout(self):
        """Setup the spacious new layout with all widgets"""

        # Left section - Large Chess Board
        board_frame = tk.Frame(self.root, bg="#1a1a1a")
        board_frame.grid(row=0, column=0, padx=(15, 10), pady=(15, 15), sticky="nsew")
        board_frame.grid_columnconfigure(0, weight=1)
        board_frame.grid_rowconfigure(0, weight=1)

        self.chess_board = ChessBoardWidget(board_frame)
        self.chess_board.grid(row=0, column=0, sticky="nsew")

        # Right section - Tabbed Information Panels
        right_frame = tk.Frame(self.root, bg="#1a1a1a")
        right_frame.grid(row=0, column=1, padx=(10, 15), pady=(15, 15), sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)

        # Create tabbed notebook
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Configure notebook style - monochromatic
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background="#1a1a1a", borderwidth=0)
        style.configure("TNotebook.Tab", background="#2a2a2a", foreground="#ffffff",
                       padding=[15, 8], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                 background=[("selected", "#404040"), ("active", "#333333")],
                 foreground=[("selected", "#ffffff"), ("active", "#ffffff")])

        # Game Info, Activity & History Tab
        game_info_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        game_info_frame.grid_columnconfigure(0, weight=1)
        game_info_frame.grid_rowconfigure(0, weight=0)  # Game info - fixed height
        game_info_frame.grid_rowconfigure(1, weight=1)  # Activity log - flexible
        game_info_frame.grid_rowconfigure(2, weight=1)  # Move history - flexible

        # Game info section (top - compact)
        self.game_info = GameInfoWidget(game_info_frame)
        self.game_info.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))

        # Activity log section (middle)
        self.log_panel = LogPanelWidget(game_info_frame)
        self.log_panel.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 2))

        # Move history section (bottom)
        self.move_history = MoveHistoryWidget(game_info_frame)
        self.move_history.grid(row=2, column=0, sticky="nsew", padx=5, pady=(2, 5))

        self.notebook.add(game_info_frame, text="Game")

        # Statistics Tab
        stats_frame = tk.Frame(self.notebook, bg="#1a1a1a")
        stats_frame.grid_columnconfigure(0, weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)

        self.stats_panel = StatisticsPanelWidget(stats_frame)
        self.stats_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.notebook.add(stats_frame, text="Statistics")

        # Bottom status bar
        self._create_status_bar()

    def _create_status_bar(self):
        """Create the bottom status bar"""
        status_frame = tk.Frame(self.root, bg="#2a2a2a", relief="flat", borderwidth=1)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 15))

        # Status indicators
        self.status_bot_mode = tk.Label(
            status_frame,
            text="🤖 AutoPlay",
            font=("Segoe UI", 9),
            fg="#cccccc",  # Light gray for active mode
            bg="#2a2a2a"
        )
        self.status_bot_mode.pack(side=tk.LEFT, padx=(15, 25))

        self.status_connection = tk.Label(
            status_frame,
            text="● Ready",
            font=("Segoe UI", 9),
            fg="#888888",  # Medium gray for status
            bg="#2a2a2a"
        )
        self.status_connection.pack(side=tk.LEFT, padx=(0, 25))

        self.status_engine = tk.Label(
            status_frame,
            text="⚙ Stockfish",
            font=("Segoe UI", 9),
            fg="#ffffff",  # White text
            bg="#2a2a2a"
        )
        self.status_engine.pack(side=tk.LEFT, padx=(0, 25))

        self.status_game = tk.Label(
            status_frame,
            text="⏸ Waiting",
            font=("Segoe UI", 9),
            fg="#ffffff",  # White text
            bg="#2a2a2a"
        )
        self.status_game.pack(side=tk.RIGHT, padx=(25, 15))

        # Initialize status based on config
        self._update_initial_status()

    def _update_initial_status(self):
        """Update status bar with initial config values"""
        if self.game_manager:
            if self.game_manager.config_manager.is_autoplay_enabled:
                self.status_bot_mode.configure(text="Mode: AutoPlay", fg="#00DD88")
            else:
                move_key = self.game_manager.config_manager.move_key
                self.status_bot_mode.configure(text=f"Mode: Manual ({move_key})", fg="#FFB347")

            engine_path = self.game_manager.config_manager.get("engine", "path", "Unknown")
            engine_name = engine_path.split("/")[-1].split("\\")[-1] if engine_path != "Unknown" else "Unknown"
            self.status_engine.configure(text=f"Engine: {engine_name}")

    def update_status_connection(self, status: str, color: str = "#888888"):
        """Update connection status"""
        self.status_connection.configure(text=f"Status: {status}", fg=color)

    def update_status_game(self, status: str, color: str = "#CCCCCC"):
        """Update game status"""
        self.status_game.configure(text=f"Game: {status}", fg=color)

    def _setup_callbacks(self):
        """Setup callbacks between components"""
        if self.game_manager:
            # Register this GUI with the game manager for updates
            self.game_manager.set_gui_callback(self.update_from_game_manager)
            
            # Register for config change notifications
            self.game_manager.config_manager.register_change_callback(self._on_config_change)

        # Auto-start the bot
        self.root.after(1000, self._auto_start_bot)

        # Update initial status
        self._update_initial_status()

    def _on_config_change(self, change_data: dict):
        """Handle config file changes - update GUI"""
        changed_sections = change_data.get("changed_sections", [])
        
        # Log to activity panel
        self.root.after(0, lambda: self.log_panel.add_log(
            f"Config reloaded: {', '.join(changed_sections)}", "success"
        ))
        
        # Update status bar if general or engine settings changed
        if "general" in changed_sections or "engine" in changed_sections:
            self.root.after(0, self._update_initial_status)

    def _auto_start_bot(self):
        """Auto-start the bot after GUI is loaded"""
        if not self.is_running and self.game_manager:
            self.is_running = True
            self.log_panel.add_log("Auto-starting chess bot...", "success")

            # Start game manager in separate thread
            threading.Thread(target=self._run_game_manager, daemon=True).start()

    def _run_game_manager(self):
        """Run the game manager in a separate thread"""
        try:
            if self.game_manager:
                self.game_manager.start()
        except Exception as e:
            self.log_panel.add_log(f"Game manager error: {e}", "error")
            self.is_running = False

    def update_from_game_manager(self, update_data: dict):
        """Update GUI from game manager events"""
        try:
            update_type = update_data.get("type")

            if update_type == "board_update":
                self.update_board(
                    update_data.get("board"), update_data.get("last_move")
                )

            elif update_type == "suggestion":
                self.update_suggestion(
                    update_data.get("move"), update_data.get("evaluation")
                )

            elif update_type == "game_info":
                self.update_game_info(update_data)
                # Update status bar with game info
                if "game_active" in update_data:
                    if update_data["game_active"]:
                        self.update_status_game("Active", "#00DD88")
                    else:
                        self.update_status_game("Waiting", "#888888")

            elif update_type == "move_played":
                evaluation_str = self._format_evaluation_for_history(
                    update_data.get("evaluation")
                )
                self.add_move_to_history(
                    update_data.get("move"),
                    update_data.get("move_number"),
                    update_data.get("is_white"),
                    evaluation_str,
                )

            elif update_type == "game_start":
                self.move_history.clear_history()

            elif update_type == "game_finished":
                self.show_game_result(update_data)

            elif update_type == "close_result_popup":
                self.close_result_popup()

            elif update_type == "log":
                self.log_panel.add_log(
                    update_data.get("message", ""), update_data.get("level", "info")
                )

            elif update_type == "statistics_update":
                self.stats_panel.update_statistics(update_data.get("stats", {}))

        except Exception as e:
            logger.error(f"GUI update error: {e}")

    def update_board(self, board: chess.Board, last_move: Optional[chess.Move] = None):
        """Update the chess board display"""
        if board:
            self.current_board = board.copy()
            self.chess_board.update_position(board, last_move)

            # Clear suggestion arrow when a move has been made
            if last_move:
                self.chess_board.clear_suggestion()
                self.current_suggestion = None

    def update_suggestion(self, move: chess.Move, evaluation: dict = None):
        """Update the current engine suggestion"""
        self.current_suggestion = move
        if move:
            self.chess_board.show_suggestion(move)
            self.game_info.update_suggestion(move, evaluation)
        else:
            self.chess_board.clear_suggestion()

    def update_game_info(self, info: dict):
        """Update game information panel"""
        self.game_info.update_info(info)

        # Update our color if provided
        if "our_color" in info:
            self.our_color = info["our_color"]
            self.chess_board.set_orientation(self.our_color)

    def add_log(self, message: str, level: str = "info"):
        """Add a log message to the log panel"""
        self.log_panel.add_log(message, level)

    def add_move_to_history(self, move: chess.Move, move_number: int, is_white: bool, evaluation: str = ""):
        """Add a move to the move history"""
        if move:
            self.move_history.add_move(move, move_number, is_white, evaluation)

    def show_game_result(self, result_data: dict):
        """Show the game result popup (non-blocking)"""
        def on_popup_close():
            # Notify game manager that user has acknowledged the result
            if self.game_manager:
                self.game_manager.acknowledge_game_result()
        
        try:
            # Use root.after to ensure we're on the main thread
            self.root.after(0, lambda: show_game_result(
                result_data, 
                parent=self.root, 
                on_close=on_popup_close
            ))
        except Exception as e:
            logger.error(f"Error showing game result: {e}")
            # Fallback - just log to console
            score = result_data.get("score", "Unknown")
            reason = result_data.get("reason", "Unknown")
            self.add_log(f"Game finished: {score} - {reason}", "success")
            # Still acknowledge even on error
            if self.game_manager:
                self.game_manager.acknowledge_game_result()
    
    def close_result_popup(self):
        """Close any open game result popup"""
        try:
            self.root.after(0, GameResultPopup.close_existing)
        except:
            pass

    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()

    def _format_evaluation_for_history(self, evaluation: dict = None) -> str:
        """Format evaluation data for display in move history"""
        if not evaluation or "score" not in evaluation:
            return ""

        score = evaluation["score"]
        try:
            # Handle different score types
            if hasattr(score, "is_mate") and score.is_mate():
                mate_in = score.mate()
                return f"M{mate_in}" if mate_in > 0 else f"M{mate_in}"

            if hasattr(score, "relative") and score.relative is not None:
                score_val = score.relative.score(mate_score=10000) / 100.0
                return f"{score_val:+.1f}"

            if hasattr(score, "white") and score.white is not None:
                score_val = score.white().score(mate_score=10000) / 100.0
                return f"{score_val:+.1f}"

            if hasattr(score, "score"):
                score_val = score.score(mate_score=10000) / 100.0
                return f"{score_val:+.1f}"

        except Exception:
            pass

        return ""

    def destroy(self):
        """Clean up and destroy the GUI"""
        if self.root:
            self.root.destroy()
