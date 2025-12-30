"""Debug utilities for troubleshooting"""

import glob
import os
import time
from typing import Optional

import chess
from loguru import logger
from selenium.webdriver.common.by import By


class DebugUtils:
    """Utilities for debugging and troubleshooting"""

    def __init__(self, debug_dir: str = "debug"):
        self.debug_dir = debug_dir
        self.setup_debug_folder()

    def setup_debug_folder(self) -> None:
        """Create debug folder and clean up old files"""
        if not os.path.exists(self.debug_dir):
            os.makedirs(self.debug_dir)
            logger.debug(f"Created debug folder: {self.debug_dir}")

        try:
            files = glob.glob(os.path.join(self.debug_dir, "*"))
            if files:
                for f in files:
                    os.remove(f)
                logger.debug(f"Cleaned up {len(files)} old debug files")
            else:
                logger.debug("No old debug files to clean up")
        except Exception as e:
            logger.warning(f"Failed to clean up debug files: {e}")

    def save_debug_info(
        self, driver, move_number: int, board: Optional[chess.Board] = None
    ) -> None:
        """Save debugging information when stuck"""
        try:
            ts = int(time.time())

            # Screenshot
            path = os.path.join(self.debug_dir, f"screenshot_move{move_number}_{ts}.png")
            driver.save_screenshot(path)
            logger.debug(f"Saved screenshot: {path}")

            # Page source
            path = os.path.join(self.debug_dir, f"page_move{move_number}_{ts}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.debug(f"Saved HTML: {path}")

            # Board state
            if board:
                path = os.path.join(self.debug_dir, f"board_move{move_number}_{ts}.txt")
                with open(path, "w") as f:
                    f.write(f"FEN: {board.fen()}\n")
                    f.write(f"Board:\n{board}\n")
                    f.write(f"Legal moves: {[str(m) for m in board.legal_moves]}\n")
                    f.write(f"Turn: {'White' if board.turn else 'Black'}\n")
                    f.write(f"Move number: {move_number}\n")
                logger.debug(f"Saved board state: {path}")

            logger.debug(f"Current URL: {driver.current_url}")

        except Exception as e:
            logger.error(f"Failed to save debug info: {e}")

    def debug_move_list_structure(self, driver) -> None:
        """Debug function to inspect move list HTML structure"""
        logger.info("=== DEBUGGING MOVE LIST STRUCTURE ===")

        selectors = [
            (".moves .move", By.CSS_SELECTOR),
            (".move-list .move", By.CSS_SELECTOR),
            (".move", By.CSS_SELECTOR),
            ("kwdb", By.CLASS_NAME),
            ("rm6", By.CLASS_NAME),
            ("l4x", By.CLASS_NAME),
        ]

        for selector, by in selectors:
            try:
                elements = driver.find_elements(by, selector)
                logger.info(f"'{selector}': {len(elements)} elements")
                for i, el in enumerate(elements[:5]):
                    try:
                        logger.info(
                            f"  [{i}] {el.tag_name} .{el.get_attribute('class')} = '{el.text.strip()}'"
                        )
                    except:
                        pass
            except Exception as e:
                logger.debug(f"'{selector}' failed: {e}")
