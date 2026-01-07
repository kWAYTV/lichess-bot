"""Turn handling logic"""

from time import sleep
from typing import Callable

import chess
from loguru import logger

from ..config import ConfigManager
from ..core.board import BoardHandler
from ..core.engine import ChessEngine
from ..core.stats import StatisticsManager
from ..input.keyboard_handler import KeyboardHandler
from ..utils.helpers import advanced_humanized_delay
from .state import GameState


class TurnHandler:
    """Handles turn logic for both players"""

    def __init__(
        self,
        config: ConfigManager,
        board_handler: BoardHandler,
        engine: ChessEngine,
        keyboard: KeyboardHandler,
        stats: StatisticsManager,
        notify_gui: Callable,
    ):
        self.config = config
        self.board_handler = board_handler
        self.engine = engine
        self.keyboard = keyboard
        self.stats = stats
        self.notify_gui = notify_gui

    def handle_our_turn(self, state: GameState, move_number: int) -> int:
        """Handle our turn, return next move number"""
        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            return self._process_existing_move(state, move_text, move_number)

        move = self._get_engine_move(state, move_number)

        if self.config.is_autoplay_enabled:
            return self._execute_auto(state, move, move_number)
        return self._handle_manual(state, move, move_number)

    def handle_opponent_turn(self, state: GameState, move_number: int) -> int:
        """Handle opponent turn, return next move number"""
        self.board_handler.clear_arrow()

        move_text = self.board_handler.check_for_move(move_number)
        if not move_text:
            return move_number

        if not self.board_handler.validate_and_push_move(
            state.board, move_text, move_number, False
        ):
            return move_number

        last_move = state.board.peek() if state.board.move_stack else None
        is_white = (move_number % 2) == 1

        self.notify_gui({
            "type": "board_update",
            "board": state.board,
            "last_move": last_move,
        })

        if last_move:
            self.notify_gui({
                "type": "move_played",
                "move": last_move,
                "move_number": move_number,
                "is_white": is_white,
            })

        return move_number + 1

    def _process_existing_move(
        self, state: GameState, move_text: str, move_number: int
    ) -> int:
        """Process a move that was already made"""
        self.board_handler.clear_arrow()

        if not self.board_handler.validate_and_push_move(
            state.board, move_text, move_number, True
        ):
            return move_number

        last_move = state.board.peek() if state.board.move_stack else None
        if last_move:
            is_white = (move_number % 2) == 1
            self.notify_gui({
                "type": "move_played",
                "move": last_move,
                "move_number": move_number,
                "is_white": is_white,
            })

        return move_number + 1

    def _get_remaining_time(self) -> int:
        """Get our remaining clock time in seconds"""
        try:
            time = self.board_handler.get_our_clock_seconds()
            if time is None:
                return 999
            return time
        except Exception:
            return 999

    def _get_engine_move(self, state: GameState, move_number: int) -> chess.Move:
        """Get best move from engine"""
        remaining = self._get_remaining_time()
        base_depth = int(self.config.get("engine", "depth", 5))
        depth = self._adjust_depth_for_time(base_depth)

        advanced_humanized_delay(self.config, "thinking", remaining)

        result = self.engine.get_best_move(state.board, depth=depth)
        move = result.move

        logger.info(f"Suggest: {move} [d={depth}]")

        eval_data = {
            "depth": depth,
            "score": getattr(result, "info", {}).get("score"),
            "pv": getattr(result, "info", {}).get("pv", []),
        }
        self.stats.add_evaluation(eval_data)

        self.notify_gui({"type": "suggestion", "move": move, "evaluation": eval_data})
        self.notify_gui({
            "type": "game_info",
            "turn": state.board.turn,
            "move_number": move_number,
        })

        return move

    def _execute_auto(
        self, state: GameState, move: chess.Move, move_number: int
    ) -> int:
        """Execute move automatically"""
        remaining = self._get_remaining_time()

        if self.config.show_arrow and remaining > 30:
            self.board_handler.draw_arrow(move, state.our_color)
            advanced_humanized_delay(self.config, "base", remaining)

        self.board_handler.execute_move(move, remaining)
        state.board.push(move)

        is_white = (move_number % 2) == 1
        self.notify_gui({"type": "board_update", "board": state.board, "last_move": move})
        self.notify_gui({
            "type": "move_played",
            "move": move,
            "move_number": move_number,
            "is_white": is_white,
        })

        return move_number + 1

    def _handle_manual(
        self, state: GameState, move: chess.Move, move_number: int
    ) -> int:
        """Handle manual move execution"""
        if state.current_suggestion != move:
            state.current_suggestion = move
            state.arrow_drawn = False

        if self.config.show_arrow and not state.arrow_drawn:
            self.board_handler.draw_arrow(move, state.our_color)
            state.arrow_drawn = True

        if not self.keyboard.should_make_move():
            logger.info(f"Suggest: {move} - press {self.config.move_key}")
            sleep(0.1)
            return move_number

        logger.info(f"Executing: {move}")
        remaining = self._get_remaining_time()
        self.board_handler.execute_move(move, remaining)
        self.keyboard.reset_move_state()
        state.board.push(move)

        state.current_suggestion = None
        state.arrow_drawn = False

        is_white = (move_number % 2) == 1
        self.notify_gui({"type": "board_update", "board": state.board, "last_move": move})
        self.notify_gui({
            "type": "move_played",
            "move": move,
            "move_number": move_number,
            "is_white": is_white,
        })

        return move_number + 1

    def _adjust_depth_for_time(self, base_depth: int) -> int:
        """Adjust engine depth based on remaining time"""
        try:
            our_time = self.board_handler.get_our_clock_seconds()
            if our_time is None:
                return base_depth

            if our_time < 10:
                depth = min(base_depth, 2)
                logger.warning(f"Critical time {our_time}s, depth={depth}")
            elif our_time < 30:
                depth = min(base_depth, 4)
            elif our_time < 60:
                depth = max(base_depth - 2, 3)
            else:
                depth = base_depth

            return depth
        except Exception:
            return base_depth
