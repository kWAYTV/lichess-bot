"""Game Info Widget - Current game state and engine information"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

import chess


class GameInfoWidget(tk.Frame):
    """Widget displaying current game information and engine suggestions"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        # State
        self.current_move = None
        self.our_color = "white"
        self.game_active = False

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all info widgets"""

        # Title
        self.title_label = tk.Label(
            self,
            text="Game Information",
            font=("Arial", 12, "bold"),  # Smaller for tabbed layout
            fg="#FFFFFF",
            bg="#1A1A1A",  # Match tab background
        )

        # Game status frame
        self.status_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.color_label = tk.Label(
            self.status_frame,
            text="Playing as: Unknown",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.turn_label = tk.Label(
            self.status_frame,
            text="Turn: White to move",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.move_number_label = tk.Label(
            self.status_frame,
            text="Move: 1",
            font=("Arial", 10),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        # Engine suggestion frame
        self.engine_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.engine_title = tk.Label(
            self.engine_frame,
            text="Engine Suggestion",
            font=("Arial", 12, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A",
        )

        self.suggestion_label = tk.Label(
            self.engine_frame,
            text="No suggestion",
            font=("Arial", 11, "bold"),
            fg="#888888",
            bg="#1A1A1A",
        )

        self.evaluation_label = tk.Label(
            self.engine_frame,
            text="Evaluation: N/A",
            font=("Arial", 10, "bold"),
            fg="#00DD88",
            bg="#1A1A1A",
        )

        self.depth_label = tk.Label(
            self.engine_frame,
            text="Depth: N/A",
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#1A1A1A",
        )

        self.best_line_label = tk.Label(
            self.engine_frame,
            text="Best line: N/A",
            font=("Arial", 9),
            fg="#CCCCCC",
            bg="#1A1A1A",
            wraplength=200,
            justify="left",
        )

    def _setup_layout(self):
        """Setup widget layout - vertical for side panel placement"""
        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label.grid(row=0, column=0, pady=(5, 8), sticky="ew")

        # Game status
        self.status_frame.grid(row=1, column=0, pady=(0, 5), padx=2, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.color_label.grid(row=0, column=0, pady=3, padx=8, sticky="w")
        self.turn_label.grid(row=1, column=0, pady=1, padx=8, sticky="w")
        self.move_number_label.grid(row=2, column=0, pady=3, padx=8, sticky="w")

        # Engine info
        self.engine_frame.grid(row=2, column=0, pady=(0, 5), padx=2, sticky="ew")
        self.engine_frame.grid_columnconfigure(0, weight=1)

        self.engine_title.grid(row=0, column=0, pady=(5, 5), sticky="ew")
        self.suggestion_label.grid(row=1, column=0, pady=1, padx=8, sticky="w")
        self.evaluation_label.grid(row=2, column=0, pady=1, padx=8, sticky="w")
        self.depth_label.grid(row=3, column=0, pady=1, padx=8, sticky="w")
        self.best_line_label.grid(row=4, column=0, pady=(1, 5), padx=8, sticky="w")

    def update_info(self, info: dict):
        """Update game information"""

        # Update color
        if "our_color" in info:
            color = info["our_color"]
            self.our_color = color
            color_text = (
                "White" if color.lower() == "white" or color == "W" else "Black"
            )
            self.color_label.configure(text=f"Playing as: {color_text}")

        # Update turn
        if "turn" in info:
            turn = info["turn"]
            turn_text = "White to move" if turn else "Black to move"
            self.turn_label.configure(text=f"Turn: {turn_text}")

        # Update move number
        if "move_number" in info:
            move_num = info["move_number"]
            self.move_number_label.configure(text=f"Move: {move_num}")

        # Update game status
        if "game_active" in info:
            self.game_active = info["game_active"]

    def update_suggestion(self, move: chess.Move, evaluation: dict = None):
        """Update engine suggestion display"""
        if move:
            # Format move nicely
            move_str = str(move)
            from_square = move_str[:2].upper()
            to_square = move_str[2:4].upper()

            # Check for promotion
            if len(move_str) > 4:
                promotion = move_str[4:].upper()
                move_display = f"{from_square} → {to_square}={promotion}"
            else:
                move_display = f"{from_square} → {to_square}"

            self.suggestion_label.configure(text=move_display, fg="#00AA00")

            # Update evaluation if provided
            if evaluation:
                eval_text = self._format_evaluation(evaluation)
                self.evaluation_label.configure(text=eval_text)

                if "depth" in evaluation:
                    depth = evaluation["depth"]
                    self.depth_label.configure(text=f"Depth: {depth}")
                else:
                    self.depth_label.configure(text="Depth: N/A")

                # Show principal variation (best line)
                if "pv" in evaluation and evaluation["pv"]:
                    pv = evaluation["pv"]
                    if pv and len(pv) > 0:
                        pv_moves = [str(m) for m in pv[:5]]  # Show first 5 moves
                        best_line = " ".join(pv_moves)
                        if len(pv) > 5:
                            best_line += " ..."
                        self.best_line_label.configure(text=f"Best line: {best_line}")
                    else:
                        self.best_line_label.configure(text="Best line: N/A")
                else:
                    self.best_line_label.configure(text="Best line: N/A")
            else:
                self.evaluation_label.configure(text="Evaluation: N/A")
                self.depth_label.configure(text="Depth: N/A")
                self.best_line_label.configure(text="Best line: N/A")
        else:
            self.suggestion_label.configure(text="No suggestion", fg="#888888")
            self.evaluation_label.configure(text="Evaluation: N/A")
            self.depth_label.configure(text="Depth: N/A")

    def _format_evaluation(self, evaluation: dict) -> str:
        """Format evaluation score with proper mate and centipawn handling"""
        if "score" not in evaluation or not evaluation["score"]:
            return "Evaluation: N/A"

        score = evaluation["score"]

        # Handle different score types
        try:
            # Check for mate scores first
            if hasattr(score, "is_mate") and score.is_mate():
                mate_in = score.mate()
                if mate_in > 0:
                    return f"Evaluation: Mate in {mate_in}"
                else:
                    return f"Evaluation: Mated in {abs(mate_in)}"

            # Handle relative scores (from white's perspective)
            if hasattr(score, "relative") and score.relative is not None:
                score_val = score.relative.score(mate_score=10000) / 100.0
                return f"Evaluation: {score_val:+.2f}"

            # Handle absolute scores
            if hasattr(score, "white") and score.white is not None:
                score_val = score.white().score(mate_score=10000) / 100.0
                return f"Evaluation: {score_val:+.2f}"

            # Fallback - try direct score access
            if hasattr(score, "score"):
                score_val = score.score(mate_score=10000) / 100.0
                return f"Evaluation: {score_val:+.2f}"

        except Exception:
            pass

        return "Evaluation: N/A"

    def clear_suggestion(self):
        """Clear the current suggestion"""
        self.update_suggestion(None)
