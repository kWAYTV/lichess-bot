"""Game state management"""

from dataclasses import dataclass, field
from typing import Optional

import chess


@dataclass
class GameState:
    """Holds current game state"""

    board: chess.Board = field(default_factory=chess.Board)
    our_color: str = "W"
    active: bool = False
    result_logged: bool = False
    waiting_for_ack: bool = False
    current_suggestion: Optional[chess.Move] = None
    arrow_drawn: bool = False

    def reset(self) -> None:
        """Reset for new game"""
        self.board.reset()
        self.active = True
        self.result_logged = False
        self.waiting_for_ack = False
        self.current_suggestion = None
        self.arrow_drawn = False

    def is_our_turn(self) -> bool:
        """Check if it's our turn"""
        return (self.board.turn and self.our_color == "W") or (
            not self.board.turn and self.our_color == "B"
        )

    @property
    def our_color_name(self) -> str:
        """Get color as full word"""
        return "white" if self.our_color == "W" else "black"
