"""Configuration Manager - Singleton pattern for config handling"""

import configparser
import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, Optional

from ..utils.helpers import get_stockfish_path


class ConfigManager:
    """Singleton configuration manager"""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    VALID_LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

    REQUIRED_FILES = [
        "config.ini",
        os.path.join("deps", "lichess.org.cookies.json"),
    ]

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._base_path = self._get_base_path()
            self._validate_required_files()
            self.config = configparser.ConfigParser()
            self._config_path = os.path.join(self._base_path, "config.ini")
            self._load_or_create_config()
            ConfigManager._initialized = True

    def _get_base_path(self) -> str:
        """Get base path for exe or script"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _validate_required_files(self) -> None:
        """Check required files exist, show error and exit if missing"""
        missing = [f for f in self.REQUIRED_FILES if not os.path.exists(os.path.join(self._base_path, f))]
        if missing:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Files", f"Required files not found:\n\n• " + "\n• ".join(missing))
            root.destroy()
            sys.exit(1)


    def _load_or_create_config(self) -> None:
        """Load existing config or create default"""
        if os.path.isfile(self._config_path):
            self.config.read(self._config_path)
        else:
            self._create_default_config()
            self.config.read(self._config_path)

    def _create_default_config(self) -> None:
        """Create default configuration"""
        self.config["engine"] = {
            "path": get_stockfish_path(),
            "depth": "5",
            "hash": "2048",
            "skill-level": "14",
        }
        self.config["general"] = {
            "move-key": "end",
            "arrow": "true",
            "auto-play": "true",
            "auto-preset": "true",
            "log-level": "INFO",
        }
        self.config["humanization"] = {
            "min-delay": "0.3",
            "max-delay": "1.8",
            "moving-min-delay": "0.5",
            "moving-max-delay": "2.5",
            "thinking-min-delay": "0.8",
            "thinking-max-delay": "3.0",
        }
        self.config["browser"] = {
            "firefox-binary-path": "",
        }

        with open(self._config_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get config value"""
        try:
            return self.config[section].get(key, fallback)
        except KeyError:
            return fallback

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire section"""
        try:
            return dict(self.config[section])
        except KeyError:
            return {}

    def set(self, section: str, key: str, value: str) -> None:
        """Set config value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self) -> None:
        """Save config to file"""
        with open(self._config_path, "w", encoding="utf-8") as f:
            self.config.write(f)

    @property
    def engine_config(self) -> Dict[str, str]:
        """Get engine configuration section"""
        return self.get_section("engine")

    @property
    def general_config(self) -> Dict[str, str]:
        """Get general configuration section"""
        return self.get_section("general")

    @property
    def humanization_config(self) -> Dict[str, str]:
        """Get humanization configuration section"""
        return self.get_section("humanization")

    @property
    def browser_config(self) -> Dict[str, str]:
        """Get browser configuration section"""
        return self.get_section("browser")

    @property
    def is_autoplay_enabled(self) -> bool:
        """Check if autoplay is enabled"""
        return self.get("general", "auto-play", "false").lower() == "true"

    @property
    def is_auto_preset_enabled(self) -> bool:
        """Check if auto-preset is enabled"""
        return self.get("general", "auto-preset", "true").lower() == "true"

    @property
    def move_key(self) -> str:
        """Get move key"""
        return self.get("general", "move-key", "end")

    @property
    def show_arrow(self) -> bool:
        """Check if arrow display is enabled"""
        return self.get("general", "arrow", "true").lower() == "true"

    @property
    def firefox_binary_path(self) -> str:
        """Get Firefox binary path"""
        return self.get("browser", "firefox-binary-path", "")

    @property
    def log_level(self) -> str:
        """Get log level"""
        level = self.get("general", "log-level", "INFO").upper()
        if level not in self.VALID_LOG_LEVELS:
            return "INFO"
        return level

    def get_humanization_delay(self, delay_type: str) -> tuple[float, float]:
        """Get delay range for humanization"""
        cfg = self.humanization_config
        delays = {
            "base": ("min-delay", "max-delay", 0.3, 1.8),
            "moving": ("moving-min-delay", "moving-max-delay", 0.5, 2.5),
            "thinking": ("thinking-min-delay", "thinking-max-delay", 0.8, 3.0),
        }

        min_key, max_key, default_min, default_max = delays.get(
            delay_type, delays["base"]
        )

        return (
            float(cfg.get(min_key, default_min)),
            float(cfg.get(max_key, default_max)),
        )
