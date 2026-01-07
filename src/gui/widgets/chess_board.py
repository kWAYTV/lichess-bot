"""Chess Board Widget - Visual chess board display"""

import ctypes
import os
import sys
import tkinter as tk
from typing import Optional

import chess


def _load_merida_font():
    """Load Chess Merida font from deps folder"""
    if sys.platform != "win32":
        return False

    # Get font path
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))))

    font_path = os.path.join(base, "deps", "merifont.ttf")

    if not os.path.exists(font_path):
        return False

    try:
        # Windows: Add font resource temporarily
        gdi32 = ctypes.windll.gdi32
        # FR_PRIVATE = 0x10 (font only available to this process)
        result = gdi32.AddFontResourceExW(font_path, 0x10, 0)
        return result > 0
    except Exception:
        return False


# Try to load font on module import
_MERIDA_LOADED = _load_merida_font()


class ChessBoardWidget(tk.Frame):
    """Professional chess board widget with position display and move arrows"""

    # Fixed margin for coordinates
    COORD_MARGIN = 16

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#2B2B2B", **kwargs)

        self.orientation = "white"

        self.light_square_color = "#4a4a4a"
        self.dark_square_color = "#2a2a2a"
        self.suggestion_color = "#666666"
        self.last_move_color = "#555555"
        self.square_outline_color = "#404040"
        self.coordinate_color = "#888888"

        self.current_board = chess.Board()
        self.last_move = None
        self.suggestion_move = None

        self.board_size = 200
        self.square_size = self.board_size // 8

        self._create_canvas()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _create_canvas(self):
        """Create the main canvas for the chess board"""
        self.canvas = tk.Canvas(
            self, bg="#2B2B2B", highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _on_canvas_resize(self, event):
        """Handle canvas resize and redraw board"""
        # Reserve space for coordinates on left and bottom
        available = min(event.width, event.height) - self.COORD_MARGIN - 4
        new_size = max(80, available)
        # Make board size divisible by 8
        new_size = (new_size // 8) * 8

        if new_size != self.board_size:
            self.board_size = new_size
            self.square_size = self.board_size // 8
            self._redraw_all()

    def _get_board_origin(self):
        """Get top-left corner of the board (after coordinate margin)"""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        # Center the board+coords in the canvas
        total_w = self.board_size + self.COORD_MARGIN
        total_h = self.board_size + self.COORD_MARGIN

        offset_x = max(0, (canvas_w - total_w) // 2)
        offset_y = max(0, (canvas_h - total_h) // 2)

        # Board starts after left margin for rank numbers
        board_x = offset_x + self.COORD_MARGIN
        board_y = offset_y

        return board_x, board_y

    def _redraw_all(self):
        """Redraw everything on the board"""
        self.canvas.delete("all")
        self._draw_board()
        self._draw_coordinates()
        self._draw_pieces()
        if self.suggestion_move:
            self._draw_suggestion_arrow()

    def _draw_board(self):
        """Draw the chess board squares"""
        start_x, start_y = self._get_board_origin()

        for rank in range(8):
            for file in range(8):
                x1 = start_x + file * self.square_size
                y1 = start_y + rank * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size

                is_light = (rank + file) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color

                if self.last_move and self._is_square_in_move(rank, file, self.last_move):
                    color = self.last_move_color

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=self.square_outline_color,
                    width=1,
                    tags="board",
                )

    def _draw_coordinates(self):
        """Draw file and rank coordinates outside the board"""
        start_x, start_y = self._get_board_origin()

        files = "abcdefgh" if self.orientation == "white" else "hgfedcba"
        ranks = "87654321" if self.orientation == "white" else "12345678"

        font_size = max(8, min(11, self.COORD_MARGIN - 4))

        # File letters below the board
        for i, file_letter in enumerate(files):
            x = start_x + i * self.square_size + self.square_size // 2
            y = start_y + self.board_size + self.COORD_MARGIN // 2 + 2
            self.canvas.create_text(
                x, y,
                text=file_letter,
                fill=self.coordinate_color,
                font=("Arial", font_size),
                tags="coordinates",
            )

        # Rank numbers to the left of the board
        for i, rank_number in enumerate(ranks):
            x = start_x - self.COORD_MARGIN // 2
            y = start_y + i * self.square_size + self.square_size // 2
            self.canvas.create_text(
                x, y,
                text=rank_number,
                fill=self.coordinate_color,
                font=("Arial", font_size),
                tags="coordinates",
            )

    def _draw_pieces(self):
        """Draw chess pieces on the board"""
        start_x, start_y = self._get_board_origin()

        # Merida font uses letters: uppercase=white, lowercase=black
        # k=king, q=queen, r=rook, b=bishop, n=knight, p=pawn
        if _MERIDA_LOADED:
            merida_symbols = {
                chess.PAWN: ("o", "p"),      # black, white
                chess.ROOK: ("t", "r"),
                chess.KNIGHT: ("m", "n"),
                chess.BISHOP: ("v", "b"),
                chess.QUEEN: ("w", "q"),
                chess.KING: ("l", "k"),
            }
            font_name = "Chess Merida"
            font_size = max(14, int(self.square_size * 0.85))
        else:
            # Fallback to Unicode symbols
            merida_symbols = {
                chess.PAWN: ("♟", "♙"),
                chess.ROOK: ("♜", "♖"),
                chess.KNIGHT: ("♞", "♘"),
                chess.BISHOP: ("♝", "♗"),
                chess.QUEEN: ("♛", "♕"),
                chess.KING: ("♚", "♔"),
            }
            font_name = "Arial"
            font_size = max(12, int(self.square_size * 0.6))

        for square in chess.SQUARES:
            piece = self.current_board.piece_at(square)
            if piece:
                file_idx = chess.square_file(square)
                rank_idx = chess.square_rank(square)

                if self.orientation == "white":
                    x = start_x + file_idx * self.square_size + self.square_size // 2
                    y = start_y + (7 - rank_idx) * self.square_size + self.square_size // 2
                else:
                    x = start_x + (7 - file_idx) * self.square_size + self.square_size // 2
                    y = start_y + rank_idx * self.square_size + self.square_size // 2

                symbol = merida_symbols[piece.piece_type][1 if piece.color else 0]

                self.canvas.create_text(
                    x, y,
                    text=symbol,
                    fill="#F5F5F5" if piece.color else "#1A1A1A",
                    font=(font_name, font_size),
                    tags="pieces",
                )

    def _draw_suggestion_arrow(self):
        """Draw an arrow for the engine suggestion"""
        if not self.suggestion_move:
            return

        start_x, start_y = self._get_board_origin()

        from_square = self.suggestion_move.from_square
        to_square = self.suggestion_move.to_square

        from_x, from_y = self._square_to_canvas_coords(from_square, start_x, start_y)
        to_x, to_y = self._square_to_canvas_coords(to_square, start_x, start_y)

        arrow_width = max(2, self.square_size // 20)
        self.canvas.create_line(
            from_x, from_y, to_x, to_y,
            fill=self.suggestion_color,
            width=arrow_width,
            arrow=tk.LAST,
            arrowshape=(16, 20, 6),
            tags="suggestion",
        )

        circle_radius = max(4, self.square_size // 15)
        self.canvas.create_oval(
            from_x - circle_radius,
            from_y - circle_radius,
            from_x + circle_radius,
            from_y + circle_radius,
            fill=self.suggestion_color,
            outline="",
            tags="suggestion",
        )

    def _square_to_canvas_coords(self, square, start_x, start_y):
        """Convert chess square to canvas coordinates"""
        file_idx = chess.square_file(square)
        rank_idx = chess.square_rank(square)

        if self.orientation == "white":
            x = start_x + file_idx * self.square_size + self.square_size // 2
            y = start_y + (7 - rank_idx) * self.square_size + self.square_size // 2
        else:
            x = start_x + (7 - file_idx) * self.square_size + self.square_size // 2
            y = start_y + rank_idx * self.square_size + self.square_size // 2

        return x, y

    def _is_square_in_move(self, rank, file, move):
        """Check if a square is part of a move (for highlighting)"""
        if self.orientation == "white":
            square = chess.square(file, 7 - rank)
        else:
            square = chess.square(7 - file, rank)

        return square in (move.from_square, move.to_square)

    def update_position(
        self, board: chess.Board, last_move: Optional[chess.Move] = None
    ):
        """Update the board position"""
        self.current_board = board.copy()
        self.last_move = last_move
        self._redraw_all()

    def show_suggestion(self, move: chess.Move):
        """Show an engine suggestion with an arrow"""
        self.suggestion_move = move
        self._draw_suggestion_arrow()

    def clear_suggestion(self):
        """Clear the suggestion arrow"""
        self.suggestion_move = None
        self.canvas.delete("suggestion")

    def set_orientation(self, color: str):
        """Set board orientation (white/black)"""
        self.orientation = color.lower()
        self._redraw_all()
