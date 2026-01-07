"""Move History Widget - Scrollable list of game moves"""

import tkinter as tk
from tkinter import ttk
from typing import List

import chess
from ...utils.logging import logger


class MoveHistoryWidget(tk.Frame):
    """Widget displaying scrollable move history"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#1e1e2e", **kwargs)

        self.moves: List[tuple] = []
        self.current_move_number = 0

        self.bg_color = "#1a1a1a"
        self.surface_color = "#2a2a2a"
        self.text_color = "#ffffff"
        self.secondary_text = "#cccccc"

        self._create_widgets()
        self._setup_layout()

    def _create_widgets(self):
        """Create all history widgets"""
        self.title_label = tk.Label(
            self,
            text="Moves",
            font=("Arial", 10, "bold"),
            fg="#FFFFFF",
            bg="#1A1A1A",
        )

        self.tree_frame = tk.Frame(self, bg="#1A1A1A", relief="solid", bd=1)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("move_num", "white", "black"),
            show="headings",
            height=8,
        )

        self.tree.heading("move_num", text="#")
        self.tree.heading("white", text="White")
        self.tree.heading("black", text="Black")

        self.tree.column("move_num", width=35, minwidth=30, anchor="center", stretch=False)
        self.tree.column("white", width=80, minwidth=50, anchor="center", stretch=True)
        self.tree.column("black", width=80, minwidth=50, anchor="center", stretch=True)

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

        self.scrollbar = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.status_label = tk.Label(
            self,
            text="No moves yet",
            font=("Arial", 9),
            fg="#888888",
            bg="#2B2B2B",
        )

        self.copy_btn = tk.Button(
            self,
            text="Copy PGN",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#3a3a4a",
            activebackground="#4a4a5a",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            command=self._copy_pgn,
        )

    def _setup_layout(self):
        """Setup widget layout"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title_label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        self.tree_frame.grid(row=1, column=0, pady=(0, 8), sticky="nsew")
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        self.status_label.grid(row=2, column=0, pady=(0, 4), sticky="ew")
        self.copy_btn.grid(row=3, column=0, pady=(0, 4), sticky="ew")

    def add_move(self, move: chess.Move, move_number: int, is_white: bool):
        """Add a move to the history"""
        move_str = str(move)
        pair_number = (move_number + 1) // 2

        if is_white:
            if pair_number > len(self.moves):
                self.moves.append((pair_number, move_str, ""))
            else:
                self.moves[pair_number - 1] = (
                    pair_number,
                    move_str,
                    self.moves[pair_number - 1][2],
                )
        else:
            if pair_number > len(self.moves):
                self.moves.append((pair_number, "", move_str))
            else:
                white_move = (
                    self.moves[pair_number - 1][1]
                    if pair_number <= len(self.moves) else ""
                )
                self.moves[pair_number - 1] = (pair_number, white_move, move_str)

        self.current_move_number = move_number
        self._refresh_display()

    def _refresh_display(self):
        """Refresh the treeview display"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for move_num, white_move, black_move in self.moves:
            self.tree.insert(
                "", "end", values=(move_num, white_move or "-", black_move or "-")
            )

        if self.moves:
            self.tree.see(self.tree.get_children()[-1])

        total = sum(1 for m in self.moves if m[1]) + sum(1 for m in self.moves if m[2])
        self.status_label.configure(
            text=f"Total moves: {total}" if total else "No moves yet"
        )

    def clear_history(self):
        """Clear all move history"""
        self.moves.clear()
        self.current_move_number = 0
        self._refresh_display()

    def get_move_count(self) -> int:
        """Get total number of moves"""
        return sum(1 for m in self.moves if m[1]) + sum(1 for m in self.moves if m[2])

    def get_pgn(self) -> str:
        """Generate PGN string from moves"""
        if not self.moves:
            return ""

        pgn_parts = []
        for move_num, white, black in self.moves:
            if white:
                pgn_parts.append(f"{move_num}. {white}")
            if black:
                pgn_parts.append(black)

        return " ".join(pgn_parts)

    def _copy_pgn(self) -> None:
        """Copy PGN to clipboard"""
        pgn = self.get_pgn()
        if not pgn:
            self._flash_button("No moves", "#ff6666")
            return

        try:
            self.clipboard_clear()
            self.clipboard_append(pgn)
            self.update()
            self._flash_button("Copied!", "#66ff66")
        except Exception as e:
            logger.error(f"Failed to copy PGN: {e}")
            self._flash_button("Error", "#ff6666")

    def _flash_button(self, text: str, color: str) -> None:
        """Temporarily change button text and color"""
        original_text = self.copy_btn.cget("text")
        original_bg = self.copy_btn.cget("bg")

        self.copy_btn.configure(text=text, bg=color)
        self.after(
            1500, lambda: self.copy_btn.configure(text=original_text, bg=original_bg)
        )
