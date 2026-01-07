"""Board Handler - Chess board interaction and move detection"""

import re
from math import ceil
from time import sleep
from typing import List, Optional

import chess
from loguru import logger
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait

from ..constants import Selectors
from ..core.browser import BrowserManager
from ..utils.debug import DebugUtils
from ..utils.helpers import advanced_humanized_delay, humanized_delay
from ..utils.resilience import element_retry, move_retry, safe_execute


class BoardHandler:
    """Handles chess board interactions and move detection"""

    def __init__(
        self,
        browser_manager: BrowserManager,
        debug_utils: DebugUtils,
        config_manager=None,
    ):
        self.browser_manager = browser_manager
        self.debug_utils = debug_utils
        self.driver = browser_manager.get_driver()
        self.config_manager = config_manager

    def wait_for_game_ready(self) -> bool:
        """Wait for game to be ready and return True if successful"""
        try:
            # Wait for game URL (not lobby)
            if not self._wait_for_game_url():
                return False

            # Wait for game board
            WebDriverWait(self.driver, 30).until(
                ec.presence_of_element_located(Selectors.GAME_BOARD_CONTAINER)
            )
            logger.debug("Game board found")

            # Wait for move input
            if not self._wait_for_move_input():
                return False

            logger.debug("Game interface ready")
            return True

        except Exception as e:
            logger.error(f"Failed to wait for game ready: {e}")
            return False

    def _wait_for_game_url(self, timeout: int = 60) -> bool:
        """Wait until we're on a game URL"""
        for _ in range(timeout):
            url = self.driver.current_url
            if self._is_game_url(url):
                return True
            sleep(1)

        logger.error("Timeout waiting for game to start - still on lobby page")
        return False

    def _is_game_url(self, url: str) -> bool:
        """Check if URL is an actual game"""
        if url in (Selectors.LICHESS_URL + "/", Selectors.LICHESS_URL_ALT + "/"):
            return False

        for pattern in Selectors.NON_GAME_URL_PATTERNS:
            if pattern in url:
                return False

        # Game IDs are typically 8+ chars
        return len(url.split("/")[-1]) >= 8

    def _wait_for_move_input(self) -> bool:
        """Wait for move input element"""
        for selector_type, selector_value in Selectors.MOVE_INPUT_SELECTORS:
            try:
                WebDriverWait(self.driver, 10).until(
                    ec.presence_of_element_located((selector_type, selector_value))
                )
                logger.debug(f"Move input found: {selector_value}")
                return True
            except:
                continue

        logger.error("Could not find move input element")
        return False

    def determine_player_color(self) -> str:
        """Determine if we're playing as White or Black"""
        is_white = self.browser_manager.check_exists_by_class(
            Selectors.ORIENTATION_WHITE
        )
        color = "W" if is_white else "B"
        logger.info(f"Playing as {'WHITE' if is_white else 'BLACK'}")
        return color

    @element_retry(max_retries=3, delay=1.0)
    def get_move_input_handle(self):
        """Get the move input element"""
        for selector_type, selector_value in Selectors.MOVE_INPUT_SELECTORS:
            try:
                WebDriverWait(self.driver, 10).until(
                    ec.presence_of_element_located((selector_type, selector_value))
                )
                element = self.driver.find_element(selector_type, selector_value)
                logger.debug(f"Move input handle found: {selector_value}")
                return element
            except:
                continue

        logger.error("Could not find move input handle")
        return None

    @move_retry(max_retries=3, delay=0.5)
    def find_move_by_alternatives(self, move_number: int):
        """Try alternative selectors to find moves"""
        # Try class-based lookup first (most reliable)
        try:
            elements = self.driver.find_elements(
                By.CLASS_NAME, Selectors.MOVE_LIST_CLASS
            )
            if len(elements) >= move_number:
                element = elements[move_number - 1]
                if element.text.strip():
                    return element
        except:
            pass

        # Try XPath alternatives
        for xpath in Selectors.get_move_xpaths(move_number):
            try:
                element = self.driver.find_element(By.XPATH, xpath)
                if element.text.strip():
                    logger.debug(f"Found move {move_number} via XPath")
                    return element
            except:
                continue

        return None

    def get_previous_moves(self, board: chess.Board) -> int:
        """Get all previous moves and update board, return current move number"""
        logger.debug("Getting previous moves from board")
        move_number = 1

        # Check if any moves exist
        if not self.find_move_by_alternatives(1):
            logger.debug("No moves found - start of game")
            return 1

        while move_number < 999:
            element = self.find_move_by_alternatives(move_number)
            if not element:
                break

            move_text = element.text.strip()
            if not move_text or move_text == "...":
                move_number += 1
                continue

            try:
                board.push_san(move_text)
                logger.debug(f"Previous move {move_number}: {move_text}")
                move_number += 1
            except Exception as e:
                logger.error(f"Invalid move '{move_text}': {e}")
                self.debug_utils.save_debug_info(self.driver, move_number, board)
                break

        logger.debug(f"Total moves processed: {move_number - 1}")
        return move_number

    def check_for_move(self, move_number: int) -> Optional[str]:
        """Check if a move exists at the given position"""
        element = self.find_move_by_alternatives(move_number)
        if element:
            text = element.text.strip()
            if text and text != "...":
                return text
        return None

    def validate_and_push_move(
        self,
        board: chess.Board,
        move_text: str,
        move_number: int,
        is_our_move: bool = False,
    ) -> bool:
        """Validate and push a move to the board"""
        try:
            test_move = board.parse_san(move_text)
            if test_move not in board.legal_moves:
                logger.warning(f"Move '{move_text}' is not legal")
                self.debug_utils.save_debug_info(self.driver, move_number, board)
                return False

            uci = board.push_san(move_text)
            who = "us" if is_our_move else "opponent"
            logger.success(f"{ceil(move_number / 2)}. {uci.uci()} [{who}]")
            return True

        except Exception as e:
            logger.error(f"Invalid move '{move_text}': {e}")
            self.debug_utils.save_debug_info(self.driver, move_number, board)
            return False

    @move_retry(max_retries=3, delay=1.0)
    def execute_move(self, move: chess.Move, move_number: int) -> None:
        """Execute a move through the interface"""
        logger.debug(f"Executing move: {move}")

        # Humanized delay
        if self.config_manager:
            advanced_humanized_delay("move execution", self.config_manager, "moving")
        else:
            humanized_delay(0.5, 1.5, "move execution")

        self.clear_arrow()

        move_handle = self.get_move_input_handle()
        if not move_handle:
            raise Exception("Could not find move input handle")

        # Input delay
        if self.config_manager:
            advanced_humanized_delay("move input", self.config_manager, "base")
        else:
            humanized_delay(0.3, 0.8, "move input")

        # Click to focus the input first
        try:
            move_handle.click()
        except Exception:
            # If click fails, try JavaScript focus
            self.browser_manager.execute_script("arguments[0].focus();", move_handle)

        if self.config_manager:
            advanced_humanized_delay("typing", self.config_manager, "base")
        else:
            humanized_delay(0.2, 0.5, "typing")

        # Try sending keys, fall back to JavaScript if needed
        try:
            move_handle.clear()
            move_handle.send_keys(str(move))
            move_handle.send_keys(Keys.RETURN)
        except Exception as e:
            logger.warning(f"Direct input failed, using JavaScript: {e}")
            # JavaScript fallback
            self.browser_manager.execute_script(
                "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                move_handle,
                str(move),
            )
            move_handle.send_keys(Keys.RETURN)

    def clear_arrow(self) -> None:
        """Clear any arrows on the board"""
        self.browser_manager.execute_script(
            'var g = document.getElementsByTagName("g")[0]; if (g) g.textContent = "";'
        )

    def draw_arrow(self, move: chess.Move, our_color: str) -> None:
        """Draw an arrow showing the suggested move"""
        move_str = str(move)
        src, dst = move_str[:2], move_str[2:]
        logger.debug(f"Drawing arrow: {src} → {dst}")

        transform = self._get_piece_transform(move, our_color)

        board_style = self.driver.find_element(*Selectors.BOARD_STYLE_CONTAINER).get_attribute("style")
        board_size = re.search(r"\d+", board_style).group()

        self._inject_arrow_svg(transform, board_size, src, dst)

    def _inject_arrow_svg(
        self, transform: List[float], board_size: str, src: str, dst: str
    ) -> None:
        """Inject arrow SVG into the page"""
        self.browser_manager.execute_script(
            """
            var x1 = arguments[0], y1 = arguments[1], x2 = arguments[2], y2 = arguments[3];
            var size = arguments[4], src = arguments[5], dst = arguments[6];

            var defs = document.getElementsByTagName("defs")[0];
            var marker = document.getElementsByTagName("marker")[0];

            if (!marker) {
                marker = document.createElementNS("http://www.w3.org/2000/svg", "marker");
                marker.setAttribute("id", "arrowhead-g");
                marker.setAttribute("orient", "auto");
                marker.setAttribute("markerWidth", "4");
                marker.setAttribute("markerHeight", "8");
                marker.setAttribute("refX", "2.05");
                marker.setAttribute("refY", "2.01");
                
                var path = document.createElement('path');
                path.setAttribute("d", "M0,0 V4 L3,2 Z");
                path.setAttribute("fill", "#15781B");
                marker.appendChild(path);
                defs.appendChild(marker);
            }

            var g = document.getElementsByTagName("g")[0];
            
            var line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute("stroke", "#15781B");
            line.setAttribute("stroke-width", "0.15625");
            line.setAttribute("stroke-linecap", "round");
            line.setAttribute("marker-end", "url(#arrowhead-g)");
            line.setAttribute("opacity", "1");
            line.setAttribute("x1", x1);
            line.setAttribute("y1", y1);
            line.setAttribute("x2", x2);
            line.setAttribute("y2", y2);
            g.appendChild(line);
            
            var dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dot.setAttribute("cx", x2);
            dot.setAttribute("cy", y2);
            dot.setAttribute("r", "0.08");
            dot.setAttribute("fill", "#FFD700");
            dot.setAttribute("fill-opacity", "0.9");
            dot.setAttribute("stroke", "#15781B");
            dot.setAttribute("stroke-width", "0.02");
            g.appendChild(dot);
            
            var pulse = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
            pulse.setAttribute("attributeName", "r");
            pulse.setAttribute("values", "0.08;0.12;0.08");
            pulse.setAttribute("dur", "2s");
            pulse.setAttribute("repeatCount", "indefinite");
            dot.appendChild(pulse);
            """,
            transform[0],
            transform[1],
            transform[2],
            transform[3],
            board_size,
            src,
            dst,
        )

    def _get_piece_transform(self, move: chess.Move, our_color: str) -> List[float]:
        """Calculate arrow coordinates for the move"""
        # Coordinate mappings
        ranks_w = {"a": -3.5, "b": -2.5, "c": -1.5, "d": -0.5, "e": 0.5, "f": 1.5, "g": 2.5, "h": 3.5}
        files_w = {1: 3.5, 2: 2.5, 3: 1.5, 4: 0.5, 5: -0.5, 6: -1.5, 7: -2.5, 8: -3.5}
        ranks_b = {"a": 3.5, "b": 2.5, "c": 1.5, "d": 0.5, "e": -0.5, "f": -1.5, "g": -2.5, "h": -3.5}
        files_b = {1: -3.5, 2: -2.5, 3: -1.5, 4: -0.5, 5: 0.5, 6: 1.5, 7: 2.5, 8: 3.5}

        ranks = ranks_w if our_color == "W" else ranks_b
        files = files_w if our_color == "W" else files_b

        move_str = str(move)
        src, dst = move_str[:2], move_str[2:]

        return [
            ranks[src[0]],
            files[int(src[1])],
            ranks[dst[0]],
            files[int(dst[1])],
        ]

    def is_game_over(self) -> bool:
        """Check if game is over"""
        return bool(
            safe_execute(
                self.browser_manager.check_exists_by_class,
                Selectors.GAME_OVER_CLASS,
                default_return=False,
                log_errors=False,
            )
        )
