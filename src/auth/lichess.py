"""Lichess Authentication - Cookie-based only"""

import time

from loguru import logger

from ..config import ConfigManager
from ..core.browser import BrowserManager


class LichessAuth:
    """Handles Lichess authentication via cookies"""

    def __init__(self, config_manager: ConfigManager, browser_manager: BrowserManager):
        self.config_manager = config_manager
        self.browser_manager = browser_manager

    def sign_in(self) -> bool:
        """Sign in to Lichess using cookies"""
        try:
            if self._try_cookie_login():
                return True

            logger.error("Cookie login failed")
            return False

        except Exception as e:
            logger.error(f"Failed during sign-in process: {e}")
            return False

    def _try_cookie_login(self) -> bool:
        """Try to login using saved cookies"""

        # Load cookies and check if we're logged in
        cookies_loaded = self.browser_manager.load_cookies()
        if not cookies_loaded:
            return False

        # Refresh the page to apply cookies
        driver = self.browser_manager.get_driver()
        driver.refresh()
        time.sleep(2)

        if self.browser_manager.is_logged_in():
            logger.success("Logged in")
            return True
        else:
            self.browser_manager.clear_cookies()
            return False
