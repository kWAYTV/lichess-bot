"""Game Manager - Main game orchestration"""

from time import sleep
from typing import Callable, Optional

from loguru import logger

from ..auth.lichess import LichessAuth
from ..config import ConfigManager, auto_apply_preset
from ..core.board import BoardHandler
from ..core.browser import BrowserManager
from ..core.engine import ChessEngine
from ..core.stats import StatisticsManager
from ..input.keyboard_handler import KeyboardHandler
from ..utils.debug import DebugUtils
from ..utils.resilience import (
    BrowserRecoveryManager,
    safe_execute,
    validate_game_state,
)
from .result import ResultHandler
from .state import GameState
from .turns import TurnHandler


class GameManager:
    """Orchestrates game flow and coordinates components"""

    def __init__(self):
        self.config = ConfigManager()
        self.config_manager = self.config  # Alias for GUI compatibility
        self.browser_manager = BrowserManager()
        self.debug = DebugUtils()
        self.board_handler = BoardHandler(
            self.browser_manager, self.debug, self.config
        )
        self.engine = ChessEngine(self.config)
        self.keyboard = KeyboardHandler(self.config)
        self.auth = LichessAuth(self.config, self.browser_manager)
        self.stats = StatisticsManager()
        self.recovery = BrowserRecoveryManager(self.browser_manager)

        self.state = GameState()
        self.gui_callback: Optional[Callable] = None

        # Initialize handlers
        self.turn_handler = TurnHandler(
            self.config,
            self.board_handler,
            self.engine,
            self.keyboard,
            self.stats,
            self._notify_gui,
        )
        self.result_handler = ResultHandler(
            self.browser_manager,
            self.stats,
            self._notify_gui,
        )

    def start(self) -> None:
        """Start the chess bot"""
        logger.info("Starting bot")
        self._log_mode()

        self.keyboard.start_listening()
        self._navigate_to_lichess()
        self._show_cookie_status()

        if not self.auth.sign_in():
            logger.error("Failed to sign in to Lichess")
            return

        self._start_new_game()

    def _log_mode(self) -> None:
        """Log current mode"""
        if self.config.is_autoplay_enabled:
            logger.info("Mode: auto-play")
        else:
            logger.info(f"Mode: manual (press {self.config.move_key})")

    def _navigate_to_lichess(self) -> None:
        """Navigate to Lichess with recovery"""
        try:
            self.browser_manager.navigate_to("https://www.lichess.org")
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            if self.recovery.attempt_browser_recovery():
                self.browser_manager.navigate_to("https://www.lichess.org")
            else:
                raise

    def _show_cookie_status(self) -> None:
        """Show cookie status"""
        info = self.browser_manager.get_cookies_info()
        if info["exists"]:
        else:
            logger.warning("No cookies found")

    def _start_new_game(self) -> None:
        """Initialize and start a new game"""
        self.state.reset()

        # Wait for any previous game over screen to clear
        self._wait_for_game_over_clear()

        if not self._wait_for_game_ready():
            return

        # Auto-detect preset from clock time
        self._apply_auto_preset()

        self._determine_color()
        self.stats.start_new_game(our_color=self.state.our_color_name)
        self._notify_gui({
            "type": "game_info",
            "our_color": self.state.our_color_name,
            "game_active": True,
        })
        self._notify_gui({"type": "game_start"})

        self._play_game()

    def _wait_for_game_over_clear(self) -> None:
        """Wait for game over screen to clear before looking for new game"""
        max_wait = 30  # Max 30 seconds
        waited = 0
        while self.board_handler.is_game_over() and waited < max_wait:
            sleep(1)
            waited += 1

    def _wait_for_game_ready(self) -> bool:
        """Wait for game to be ready - polls continuously"""
        logger.info("Waiting for game...")
        poll_interval = 3  # seconds between checks

        while True:
            try:
                if self.board_handler.wait_for_game_ready():
                    return True
                sleep(poll_interval)
            except Exception as e:
                if not self.recovery.is_browser_healthy():
                    if not self.recovery.attempt_browser_recovery():
                        return False
                sleep(poll_interval)

    def _apply_auto_preset(self) -> None:
        """Auto-detect and apply preset based on clock time"""
        if not self.config.is_auto_preset_enabled:
            return

        try:
            initial_time = self.board_handler.get_our_clock_seconds()
            if initial_time:
                preset_name = auto_apply_preset(self.config, initial_time)
                logger.info(f"Preset: {preset_name} ({initial_time}s)")
                self._notify_gui({
                    "type": "preset_applied",
                    "preset": preset_name,
                    "initial_time": initial_time,
                })
        except Exception as e:

    def _determine_color(self) -> None:
        """Determine player color"""
        try:
            self.state.our_color = self.board_handler.determine_player_color()
        except Exception as e:
            logger.error(f"Color detection failed: {e}")
            self.state.our_color = "W"

    def _play_game(self) -> None:
        """Main game loop"""
        move_number = self.board_handler.get_previous_moves(self.state.board)
        self.browser_manager.save_cookies()

        self._log_game_start(move_number)

        errors = 0
        while not self.board_handler.is_game_over():
            try:
                move_number = self._game_tick(move_number)
                errors = 0
            except Exception as e:
                errors += 1
                logger.error(f"Game loop error ({errors}): {e}")

                if errors >= 5:
                    logger.error("Too many errors, exiting")
                    break

                if not self.recovery.is_browser_healthy():
                    if not self.recovery.attempt_browser_recovery():
                        break
                sleep(2)

        self._handle_game_end()

    def _log_game_start(self, move_number: int) -> None:
        """Log game start info"""
        if move_number > 1:
            logger.info(f"Joined at move {move_number}")

    def _game_tick(self, move_number: int) -> int:
        """Single game loop iteration"""
        if not validate_game_state(self.state.board, move_number):
            logger.warning("State validation failed")
            self.debug.save_debug_info(
                self.browser_manager.get_driver(), move_number, self.state.board
            )

            if self.recovery.is_browser_healthy():
                self.browser_manager.get_driver().refresh()
                sleep(5)
            return move_number

        prev = move_number

        if self.state.is_our_turn():
            move_number = self.turn_handler.handle_our_turn(self.state, move_number)
        else:
            move_number = self.turn_handler.handle_opponent_turn(self.state, move_number)

        if move_number == prev:
            sleep(0.1)

        return move_number

    def _handle_game_end(self) -> None:
        """Handle game end"""

        if not self.state.result_logged:
            self.result_handler.log_result(self.state)
            self.state.result_logged = True
            self.state.waiting_for_ack = True

            while self.state.waiting_for_ack:
                sleep(0.5)

        self._start_new_game()

    def set_gui_callback(self, callback: Callable) -> None:
        """Set GUI update callback"""
        self.gui_callback = callback

    def acknowledge_game_result(self) -> None:
        """Called when user acknowledges result"""
        self.state.waiting_for_ack = False

    def _notify_gui(self, data: dict) -> None:
        """Notify GUI of updates"""
        if self.gui_callback:
            try:
                self.gui_callback(data)
            except Exception as e:
                logger.error(f"GUI callback error: {e}")

    def cleanup(self) -> None:
        """Clean up resources"""

        safe_execute(self.keyboard.stop_listening, log_errors=True)
        safe_execute(self.engine.quit, log_errors=True)
        safe_execute(self.browser_manager.close, log_errors=True)

        logger.info("Stopped")

