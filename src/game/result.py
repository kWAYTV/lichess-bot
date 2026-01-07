"""Game result handling"""

from typing import Callable

from loguru import logger
from selenium.webdriver.common.by import By

from ..constants import Selectors
from ..core.browser import BrowserManager
from ..core.stats import StatisticsManager
from .state import GameState


class ResultHandler:
    """Handles game result detection and logging"""

    def __init__(
        self,
        browser: BrowserManager,
        stats: StatisticsManager,
        notify_gui: Callable,
    ):
        self.browser = browser
        self.stats = stats
        self.notify_gui = notify_gui

    def log_result(self, state: GameState) -> None:
        """Log and notify game result"""
        try:
            driver = self.browser.get_driver()

            score_el = driver.find_element(*Selectors.RESULT_SCORE)
            score = score_el.text if score_el else "Unknown"

            reason_el = driver.find_element(*Selectors.RESULT_REASON)
            reason = reason_el.text if reason_el else "Unknown"

            logger.success(f"Game finished: {score} - {reason}")

            move_count = len(state.board.move_stack)
            result = self._determine_result(score, state.our_color_name)

            self.stats.end_current_game(
                result=result,
                score=score,
                reason=reason,
                total_moves=move_count,
            )

            self.notify_gui({
                "type": "game_finished",
                "score": score,
                "reason": reason,
                "our_color": state.our_color_name,
                "move_count": move_count,
            })

            # Send updated stats
            overall = self.stats.get_overall_stats()
            overall["recent_games"] = self.stats.get_recent_games(5)
            self.notify_gui({"type": "statistics_update", "stats": overall})

        except Exception as e:
            logger.info("Game finished")

            self.notify_gui({
                "type": "game_finished",
                "score": "Game completed",
                "reason": "Details unavailable",
                "our_color": state.our_color_name,
                "move_count": len(state.board.move_stack),
            })

    def _determine_result(self, score: str, our_color: str) -> str:
        """Determine result from score"""
        if score == "1-0":
            return "win" if our_color == "white" else "loss"
        elif score == "0-1":
            return "win" if our_color == "black" else "loss"
        elif score == "1/2-1/2":
            return "draw"
        return "unknown"

