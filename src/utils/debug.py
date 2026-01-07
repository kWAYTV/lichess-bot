"""Debug utilities for troubleshooting"""

import glob
import os
import time
from typing import Optional

import chess
from .logging import logger
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

        try:
            files = glob.glob(os.path.join(self.debug_dir, "*"))
            if files:
                for f in files:
                    os.remove(f)
        except Exception as e:
            logger.warning(f"Failed to clean up debug files: {e}")

    def save_debug_info(
        self, driver, move_number: int, board: Optional[chess.Board] = None
    ) -> None:
        """Save debugging information when stuck"""
        try:
            ts = int(time.time())

            path = os.path.join(self.debug_dir, f"screenshot_move{move_number}_{ts}.png")
            driver.save_screenshot(path)

            path = os.path.join(self.debug_dir, f"page_move{move_number}_{ts}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(driver.page_source)

            if board:
                path = os.path.join(self.debug_dir, f"board_move{move_number}_{ts}.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(f"FEN: {board.fen()}\n")
                    f.write(f"Board:\n{board}\n")
                    f.write(f"Legal moves: {[str(m) for m in board.legal_moves]}\n")
                    f.write(f"Turn: {'White' if board.turn else 'Black'}\n")
                    f.write(f"Move number: {move_number}\n")

        except Exception as e:
            logger.error(f"Failed to save debug info: {e}")

    def debug_move_list_structure(self, driver) -> None:
        """Debug function to inspect move list HTML structure"""
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
                driver.find_elements(by, selector)
            except Exception:
                pass
