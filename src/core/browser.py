"""Browser Manager - Singleton pattern for WebDriver management"""

import json
import os
from typing import Optional

from ..utils.logging import logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from ..config.manager import ConfigManager
from ..constants import Selectors
from ..utils.helpers import get_geckodriver_path, install_firefox_extensions
from ..utils.resilience import browser_retry, element_retry


def find_firefox_binary() -> Optional[str]:
    """Find Firefox binary path on the system"""
    import shutil

    common_paths = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        r"C:\Program Files\Firefox Developer Edition\firefox.exe",
        r"C:\Program Files (x86)\Firefox Developer Edition\firefox.exe",
        r"C:\Firefox\firefox.exe",
        r"D:\Firefox\firefox.exe",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    try:
        result = shutil.which("firefox")
        if result:
            return result
    except Exception:
        pass

    logger.warning("Firefox not found")
    return None


class BrowserManager:
    """Singleton browser manager for the chess bot"""

    _instance: Optional["BrowserManager"] = None
    _initialized: bool = False

    COOKIES_FILE = os.path.join("deps", "lichess.org.cookies.json")

    def __new__(cls) -> "BrowserManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.driver: Optional[webdriver.Firefox] = None
            self._setup_driver()
            BrowserManager._initialized = True

    def _setup_driver(self) -> None:
        """Initialize Firefox WebDriver"""
        try:
            config = ConfigManager()
            firefox_binary = config.firefox_binary_path or find_firefox_binary()

            options = webdriver.FirefoxOptions()
            if firefox_binary:
                options.binary_location = firefox_binary

            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
                "Gecko/20100101 Firefox/109.0"
            )
            options.add_argument(f'--user-agent="{user_agent}"')

            service = webdriver.firefox.service.Service(
                executable_path=get_geckodriver_path()
            )

            self.driver = webdriver.Firefox(service=service, options=options)
            install_firefox_extensions(self.driver)

        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def get_driver(self) -> webdriver.Firefox:
        """Get the WebDriver instance"""
        if self.driver is None:
            raise RuntimeError("WebDriver not initialized")
        return self.driver

    @browser_retry(max_retries=3, delay=2.0)
    def navigate_to(self, url: str) -> None:
        """Navigate to a URL"""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.driver.get(url)

    @element_retry(max_retries=2, delay=0.5)
    def check_exists_by_xpath(self, xpath: str):
        """Check if element exists by XPath"""
        try:
            return self.driver.find_element(By.XPATH, xpath)
        except NoSuchElementException:
            return False

    @element_retry(max_retries=2, delay=0.5)
    def check_exists_by_class(self, classname: str):
        """Check if element exists by class name"""
        try:
            return self.driver.find_element(By.CLASS_NAME, classname)
        except NoSuchElementException:
            return False

    def execute_script(self, script: str, *args):
        """Execute JavaScript in the browser"""
        return self.driver.execute_script(script, *args)

    def save_screenshot(self, filename: str) -> None:
        """Save a screenshot"""
        if self.driver:
            self.driver.save_screenshot(filename)

    @property
    def page_source(self) -> str:
        """Get page source"""
        return self.driver.page_source if self.driver else ""

    @property
    def current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url if self.driver else ""

    def save_cookies(self) -> None:
        """Save current cookies to file"""
        if not self.driver:
            return
        try:
            cookies = self.driver.get_cookies()
            with open(self.COOKIES_FILE, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")

    def load_cookies(self) -> bool:
        """Load cookies from file"""
        if not os.path.exists(self.COOKIES_FILE):
            return False

        try:
            with open(self.COOKIES_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)

            if not self.driver or not self.current_url.startswith("https://lichess.org"):
                return False

            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception:
                    pass

            return True

        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False

    def clear_cookies(self) -> None:
        """Clear cookies"""
        try:
            if self.driver:
                self.driver.delete_all_cookies()
            if os.path.exists(self.COOKIES_FILE):
                os.remove(self.COOKIES_FILE)
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")

    def get_cookies_info(self) -> dict:
        """Get cookie file info"""
        if not os.path.exists(self.COOKIES_FILE):
            return {"exists": False, "count": 0, "file_size": 0}

        try:
            with open(self.COOKIES_FILE, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            return {
                "exists": True,
                "count": len(cookies),
                "file_size": os.path.getsize(self.COOKIES_FILE),
                "file_path": self.COOKIES_FILE,
            }
        except Exception as e:
            return {"exists": True, "count": 0, "error": str(e)}

    def is_logged_in(self) -> bool:
        """Check if logged in to Lichess"""
        if not self.driver:
            return False

        try:
            for selector in Selectors.LOGIN_INDICATORS:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if el and el.text.strip():
                        return True
                except Exception:
                    continue

            source = self.driver.page_source.lower()
            if any(ind in source for ind in Selectors.LOGIN_PAGE_INDICATORS):
                return True

            return False

        except Exception:
            return False

    def close(self) -> None:
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
