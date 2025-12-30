"""Game Manager - Main game flow and logic orchestration"""

from time import sleep

import chess
from loguru import logger
from selenium.webdriver.common.by import By

from ..auth.lichess import LichessAuth
from ..config import ConfigManager
from ..core.board import BoardHandler
from ..core.browser import BrowserManager
from ..core.engine import ChessEngine
from ..core.stats import StatisticsManager
from ..input.keyboard_handler import KeyboardHandler
from ..utils.debug import DebugUtils
from ..utils.helpers import advanced_humanized_delay
from ..utils.resilience import (
    BrowserRecoveryManager,
    safe_execute,
    validate_game_state,
)


class GameManager:
    """Manages the overall game flow and coordinates all components"""

    def __init__(self):
        # Initialize all components
        self.config_manager = ConfigManager()
        self.browser_manager = BrowserManager()
        self.debug_utils = DebugUtils()
        self.board_handler = BoardHandler(
            self.browser_manager, self.debug_utils, self.config_manager
        )
        self.chess_engine = ChessEngine(self.config_manager)
        self.keyboard_handler = KeyboardHandler(self.config_manager)
        self.lichess_auth = LichessAuth(self.config_manager, self.browser_manager)
        self.stats_manager = StatisticsManager()

        # Initialize resilience components
        self.browser_recovery_manager = BrowserRecoveryManager(self.browser_manager)

        self.board = chess.Board()
        self.current_game_active = False
        self._current_suggestion = None
        self._arrow_drawn = False
        self._game_result_logged = False  # Prevent duplicate result logging
        self._waiting_for_user_ack = False  # Wait for user to acknowledge game end

        # GUI integration
        self.gui_callback = None

    def start(self) -> None:
        """Start the chess bot application"""
        logger.info("Starting chess bot application")

        # Log current configuration
        if self.config_manager.is_autoplay_enabled:
            logger.info("AutoPlay MODE: Bot will make moves automatically")
        else:
            move_key = self.config_manager.move_key
            logger.info(
                f"Suggestion MODE: Bot will suggest moves (press '{move_key}' to execute)"
            )

        # Start keyboard listener
        # Keyboard listener started silently
        self.keyboard_handler.start_listening()

        # Navigate to Lichess with recovery
        # Navigation handled silently
        try:
            self.browser_manager.navigate_to("https://www.lichess.org")
        except Exception as e:
            logger.error(f"Failed to navigate to Lichess: {e}")
            if self.browser_recovery_manager.attempt_browser_recovery():
                logger.info("Retrying navigation after browser recovery")
                self.browser_manager.navigate_to("https://www.lichess.org")
            else:
                raise

        # Show cookie status
        cookie_info = self.browser_manager.get_cookies_info()
        if cookie_info["exists"]:
            logger.debug(
                f"Found saved cookies ({cookie_info['count']} cookies, {cookie_info['file_size']} bytes)"
            )
        else:
            logger.debug("No saved cookies found - will use username/password login")

        # Sign in
        if not self.lichess_auth.sign_in():
            logger.error("Failed to sign in to Lichess")
            return

        # Start game loop
        logger.info("Waiting for game to start")
        self.start_new_game()

    def start_new_game(self) -> None:
        """Start a new game with enhanced error handling"""
        logger.debug("Starting new game - resetting board")
        self.board.reset()
        self.current_game_active = True
        self._game_result_logged = False  # Reset the flag for new game
        self._waiting_for_user_ack = False  # Reset waiting flag for new game

        # Wait for game to be ready with retries
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if self.board_handler.wait_for_game_ready():
                    break
                else:
                    logger.warning(
                        f"Game ready attempt {attempt + 1}/{max_attempts} failed"
                    )
                    if attempt < max_attempts - 1:
                        sleep(2)
                    else:
                        logger.error("Failed to wait for game ready after all attempts")
                        return
            except Exception as e:
                logger.error(
                    f"Error waiting for game ready (attempt {attempt + 1}): {e}"
                )
                if (
                    attempt < max_attempts - 1
                    and self.browser_recovery_manager.attempt_browser_recovery()
                ):
                    logger.info("Retrying after browser recovery")
                    continue
                else:
                    logger.error("Failed to start new game")
                    return

        # Determine our color with fallback
        try:
            our_color = self.board_handler.determine_player_color()
        except Exception as e:
            logger.error(f"Failed to determine player color: {e}")
            logger.warning("Assuming we're playing as White")
            our_color = "W"

        # Store our color for result interpretation
        self._our_color = our_color

        # Start statistics tracking for this game
        color_name = "white" if our_color == "W" else "black"
        self.stats_manager.start_new_game(our_color=color_name)

        # Notify GUI of game info
        self._notify_gui(
            {
                "type": "game_info",
                "our_color": "white" if our_color == "W" else "black",
                "game_active": True,
            }
        )

        # Clear move history for new game
        self._notify_gui({"type": "game_start"})

        # Start playing with enhanced error handling
        try:
            self.play_game(our_color)
        except Exception as e:
            logger.error(f"Game play failed: {e}")
            self.debug_utils.save_debug_info(self.browser_manager.driver, 0, self.board)
            # Attempt recovery and restart
            if self.browser_recovery_manager.attempt_browser_recovery():
                logger.info("Attempting to restart game after recovery")
                self.start_new_game()
            else:
                logger.error("Could not recover from game error")

    def play_game(self, our_color: str) -> None:
        """Main game playing loop"""
        # Get previous moves to sync board state
        move_number = self.board_handler.get_previous_moves(self.board)

        # Save cookies after successful game start (indicates successful login)
        # Cookies saved silently
        self.browser_manager.save_cookies()

        # If this is the very start of the game, log our turn status
        if move_number == 1:
            if our_color == "W":
                logger.info("Starting fresh game as White - we move first")
            else:
                logger.info(
                    "Starting fresh game as Black - waiting for White's first move"
                )
        else:
            # Joined game in progress - check if it's immediately our turn
            if self._is_our_turn(our_color):
                logger.info(
                    f"Joined game in progress - it's our turn to play move {move_number}"
                )
            else:
                logger.info(
                    f"Joined game in progress - waiting for opponent's move {move_number}"
                )

        # Main game loop with enhanced error handling
        consecutive_errors = 0
        max_consecutive_errors = 5

        while not self.board_handler.is_game_over():
            try:
                # Validate game state periodically
                if not validate_game_state(self.board, move_number):
                    logger.warning("Game state validation failed, attempting recovery")
                    self.debug_utils.save_debug_info(
                        self.browser_manager.driver, move_number, self.board
                    )

                    # Try to recover by refreshing the page
                    if self.browser_recovery_manager.is_browser_healthy():
                        logger.info("Attempting page refresh to recover game state")
                        self.browser_manager.driver.refresh()
                        sleep(5)  # Wait for page to load
                        continue
                    else:
                        logger.error("Browser not healthy, attempting recovery")
                        if not self.browser_recovery_manager.attempt_browser_recovery():
                            logger.error("Could not recover browser, exiting game")
                            break

                our_turn = self._is_our_turn(our_color)
                previous_move_number = move_number

                if our_turn:
                    move_number = self._handle_our_turn(move_number, our_color)
                else:
                    move_number = self._handle_opponent_turn(move_number)

                # Prevent infinite loops
                if move_number == previous_move_number:
                    sleep(0.1)

                # Reset error counter on successful iteration
                consecutive_errors = 0

            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in game loop (attempt {consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(
                        f"Too many consecutive errors ({consecutive_errors}), exiting game"
                    )
                    self.debug_utils.save_debug_info(
                        self.browser_manager.driver, move_number, self.board
                    )
                    break

                # Try browser recovery for critical errors
                if not self.browser_recovery_manager.is_browser_healthy():
                    logger.warning("Browser unhealthy, attempting recovery")
                    if self.browser_recovery_manager.attempt_browser_recovery():
                        logger.info("Browser recovery successful, continuing game")
                        continue
                    else:
                        logger.error("Browser recovery failed, exiting game")
                        break

                # Small delay before retrying
                sleep(2)

        # Game complete
        logger.debug("Game completed - follow-up element detected")
        if not self._game_result_logged:
            self._log_game_result()
            self._game_result_logged = True
            self._waiting_for_user_ack = True
            logger.info("Game complete. Waiting for user to acknowledge result.")

            # Wait for user to acknowledge the result OR detect new game started
            # Store current URL to detect when a new game starts
            game_end_url = self.browser_manager.driver.current_url
            while self._waiting_for_user_ack:
                sleep(0.3)  # Poll every 300ms
                
                # Check if we've navigated to a new game (URL changed to different game ID)
                try:
                    current_url = self.browser_manager.driver.current_url
                    if current_url != game_end_url and self._looks_like_game_url(current_url):
                        logger.info("New game detected - auto-closing result popup")
                        self._waiting_for_user_ack = False
                        # Close the popup via GUI callback
                        self._notify_gui({"type": "close_result_popup"})
                        break
                except Exception:
                    pass  # Browser might be in transition, ignore

            logger.debug("Proceeding to new game detection.")

        # Start new game - this will either succeed (starting a new loop)
        # or fail (returning to main app loop)
        self.start_new_game()

    def _is_our_turn(self, our_color: str) -> bool:
        """Check if it's our turn to move"""
        return (self.board.turn and our_color == "W") or (
            not self.board.turn and our_color == "B"
        )

    def _notify_move_played(self, move: chess.Move, move_number: int) -> None:
        """Notify GUI of a move being played (reduces duplication)"""
        is_white = (move_number % 2) == 1
        self._notify_gui({"type": "board_update", "board": self.board, "last_move": move})
        self._notify_gui({
            "type": "move_played",
            "move": move,
            "move_number": move_number,
            "is_white": is_white,
        })

    def _looks_like_game_url(self, url: str) -> bool:
        """Check if URL looks like a Lichess game URL"""
        if not url:
            return False
        # Exclude non-game URLs
        excluded = ["/tournament", "/study", "/training", "/lobby", "/swiss"]
        if any(ex in url for ex in excluded):
            return False
        # Game IDs are typically 8+ alphanumeric chars at the end
        parts = url.rstrip("/").split("/")
        if parts:
            last_part = parts[-1].split("?")[0]  # Remove query params
            return len(last_part) >= 8 and last_part.isalnum()
        return False

    def _handle_our_turn(self, move_number: int, our_color: str) -> int:
        """Handle our turn logic"""
        # Check if we already made the move
        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            self.board_handler.clear_arrow()

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, True
            ):
                last_move = self.board.peek() if self.board.move_stack else None
                if last_move:
                    self._notify_move_played(last_move, move_number)
                return move_number + 1
            else:
                return move_number

        # Get best move from engine
        engine_depth = self.config_manager.get_with_aliases(
            "engine", ["depth", "Depth"], 5
        )
        advanced_humanized_delay("engine thinking", self.config_manager, "thinking")

        result = self.chess_engine.get_best_move(self.board)
        move_str = str(result.move)
        src_square = move_str[:2]
        dst_square = move_str[2:]
        logger.info(f"Engine suggests: {result.move} ({src_square} → {dst_square})")

        # Prepare evaluation data
        evaluation_data = {
            "depth": engine_depth,
            "score": getattr(result, "info", {}).get("score"),
            "pv": getattr(result, "info", {}).get("pv", []),
        }

        # Track evaluation in statistics
        self.stats_manager.add_evaluation(evaluation_data)

        # Notify GUI of suggestion
        self._notify_gui(
            {
                "type": "suggestion",
                "move": result.move,
                "evaluation": evaluation_data,
            }
        )

        # Update game info
        self._notify_gui(
            {"type": "game_info", "turn": self.board.turn, "move_number": move_number}
        )

        # Handle move execution based on mode
        if self.config_manager.is_autoplay_enabled:
            return self._execute_auto_move(result.move, move_number, our_color)
        else:
            return self._handle_manual_move(result.move, move_number, our_color)

    def _execute_auto_move(
        self, move: chess.Move, move_number: int, our_color: str
    ) -> int:
        """Execute move automatically"""
        logger.debug(f"Making move: {move}")

        # Show arrow briefly if enabled, even in autoplay
        if self.config_manager.show_arrow:
            logger.debug("Showing move arrow before auto execution")
            self.board_handler.draw_arrow(move, our_color)
            # Brief delay to show the arrow
            advanced_humanized_delay("showing arrow", self.config_manager, "base")

        self.board_handler.execute_move(move, move_number)
        self.board.push(move)
        self._notify_move_played(move, move_number)

        return move_number + 1

    def _handle_manual_move(
        self, move: chess.Move, move_number: int, our_color: str
    ) -> int:
        """Handle manual move execution"""
        # Show arrow if enabled (only draw once per turn)
        if not hasattr(self, "_current_suggestion") or self._current_suggestion != move:
            self._current_suggestion = move
            self._arrow_drawn = False

        if self.config_manager.show_arrow and not self._arrow_drawn:
            logger.debug("Showing move suggestion arrow")
            self.board_handler.draw_arrow(move, our_color)
            self._arrow_drawn = True

        # Check for key press
        if self.keyboard_handler.should_make_move():
            logger.info(f"Manual key press detected - making move: {move}")

            self.board_handler.execute_move(move, move_number)
            self.keyboard_handler.reset_move_state()
            self.board.push(move)

            # Reset suggestion tracking
            self._current_suggestion = None
            self._arrow_drawn = False

            self._notify_move_played(move, move_number)
            return move_number + 1
        else:
            # Just suggesting - show the move and wait
            move_key = self.config_manager.move_key
            move_str = str(move)
            src_square = move_str[:2]
            dst_square = move_str[2:]
            logger.debug(
                f"Suggesting move: {move} ({src_square} → {dst_square}) (press {move_key} to execute)"
            )
            logger.info(
                f"Suggest move: {move} ({src_square} → {dst_square}) - press {move_key} to execute"
            )
            sleep(0.1)  # Small delay to avoid spam

            return move_number

    def _handle_opponent_turn(self, move_number: int) -> int:
        """Handle opponent's turn"""
        self.board_handler.clear_arrow()

        move_text = self.board_handler.check_for_move(move_number)
        if move_text:
            logger.info(f"Opponent move detected at position {move_number}")

            if self.board_handler.validate_and_push_move(
                self.board, move_text, move_number, False
            ):
                last_move = self.board.peek() if self.board.move_stack else None
                if last_move:
                    self._notify_move_played(last_move, move_number)
                return move_number + 1

        return move_number

    def _determine_game_result(self, score: str, our_color: str) -> str:
        """Determine game result from score and our color"""
        try:
            # Lichess scores are in format like "1-0", "0-1", "1/2-1/2"
            if score == "1-0":
                return "win" if our_color == "white" else "loss"
            elif score == "0-1":
                return "win" if our_color == "black" else "loss"
            elif score == "1/2-1/2":
                return "draw"
            else:
                logger.warning(f"Unknown score format: {score}")
                return "unknown"
        except Exception as e:
            logger.error(f"Failed to determine game result: {e}")
            return "unknown"

    def _log_game_result(self) -> None:
        """Log the game result when game ends"""
        try:
            # Get score using driver directly
            score_element = self.browser_manager.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[1]"
            )
            score = score_element.text if score_element else "Score not found"

            # Get result reason using driver directly
            result_element = self.browser_manager.driver.find_element(
                By.XPATH, "/html/body/div[2]/main/div[1]/rm6/l4x/div/p[2]"
            )
            result = result_element.text if result_element else "Result not found"

            logger.success(f"GAME FINISHED - {score} | {result}")

            # Get our color for result interpretation
            our_color = (
                "white"
                if hasattr(self, "_our_color") and self._our_color == "W"
                else "black"
            )

            # Get move count from history
            move_count = len(self.board.move_stack)

            # Determine result from our perspective
            game_result = self._determine_game_result(score, our_color)

            # Record game completion in statistics
            self.stats_manager.end_current_game(
                result=game_result,
                score=score,
                reason=result,
                total_moves=move_count
            )

            # Notify GUI of game completion
            self._notify_gui(
                {
                    "type": "game_finished",
                    "score": score,
                    "reason": result,
                    "our_color": our_color,
                    "move_count": move_count,
                }
            )

            # Send updated statistics to GUI
            overall_stats = self.stats_manager.get_overall_stats()
            recent_games = self.stats_manager.get_recent_games(5)
            overall_stats["recent_games"] = recent_games

            self._notify_gui(
                {
                    "type": "statistics_update",
                    "stats": overall_stats,
                }
            )

        except Exception as e:
            logger.debug(f"Could not extract game result: {e}")
            logger.info("GAME FINISHED - Result details not available")

            # Still notify GUI even if we couldn't get details
            self._notify_gui(
                {
                    "type": "game_finished",
                    "score": "Game completed",
                    "reason": "Result details not available",
                    "our_color": getattr(self, "_our_color", "unknown"),
                    "move_count": len(self.board.move_stack) if self.board else 0,
                }
            )

    def set_gui_callback(self, callback):
        """Set the GUI callback for updates"""
        self.gui_callback = callback

    def acknowledge_game_result(self):
        """Called by GUI when user acknowledges the game result"""
        self._waiting_for_user_ack = False
        logger.debug("Game result acknowledged by user")

    def _notify_gui(self, update_data: dict):
        """Notify GUI of updates"""
        if self.gui_callback:
            try:
                self.gui_callback(update_data)
            except Exception as e:
                logger.error(f"GUI callback error: {e}")

    def cleanup(self) -> None:
        """Clean up resources with enhanced error handling"""
        logger.info("Cleaning up resources")

        # Clean up keyboard handler
        if self.keyboard_handler:
            safe_execute(
                self.keyboard_handler.stop_listening,
                log_errors=True,
                default_return=None,
            )

        # Clean up chess engine
        if self.chess_engine:
            safe_execute(self.chess_engine.quit, log_errors=True, default_return=None)

        # Clean up browser
        if self.browser_manager:
            safe_execute(
                self.browser_manager.close, log_errors=True, default_return=None
            )

        logger.info("Resource cleanup completed")
