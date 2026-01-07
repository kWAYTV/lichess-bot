"""Configuration Manager - Singleton pattern for config handling"""

import configparser
import os
from typing import Any, Dict, Optional

from loguru import logger

from ..utils.helpers import get_stockfish_path


class ConfigManager:
    """Singleton configuration manager"""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    VALID_LOG_LEVELS = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = configparser.ConfigParser()
            self._config_path = "config.ini"
            self._load_or_create_config()
            ConfigManager._initialized = True

    def _load_or_create_config(self) -> None:
        """Load existing config or create default"""
        if os.path.isfile(self._config_path):
            self.config.read(self._config_path)
            logger.debug("Loaded config.ini")
        else:
            logger.debug("Creating default config.ini")
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
            "gui-enabled": "true",
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

        with open(self._config_path, "w") as f:
            self.config.write(f)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get config value"""
        try:
            return self.config[section].get(key, fallback)
        except KeyError:
            logger.warning(f"Section '{section}' not found")
            return fallback

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire section"""
        try:
            return dict(self.config[section])
        except KeyError:
            logger.warning(f"Section '{section}' not found")
            return {}

    def set(self, section: str, key: str, value: str) -> None:
        """Set config value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self) -> None:
        """Save config to file"""
        with open(self._config_path, "w") as f:
            self.config.write(f)

    # Properties

    @property
    def engine_config(self) -> Dict[str, str]:
        return self.get_section("engine")

    @property
    def general_config(self) -> Dict[str, str]:
        return self.get_section("general")

    @property
    def humanization_config(self) -> Dict[str, str]:
        return self.get_section("humanization")

    @property
    def browser_config(self) -> Dict[str, str]:
        return self.get_section("browser")

    @property
    def is_autoplay_enabled(self) -> bool:
        return self.get("general", "auto-play", "false").lower() == "true"

    @property
    def is_auto_preset_enabled(self) -> bool:
        return self.get("general", "auto-preset", "true").lower() == "true"

    @property
    def move_key(self) -> str:
        return self.get("general", "move-key", "end")

    @property
    def show_arrow(self) -> bool:
        return self.get("general", "arrow", "true").lower() == "true"

    @property
    def firefox_binary_path(self) -> str:
        return self.get("browser", "firefox-binary-path", "")

    @property
    def log_level(self) -> str:
        level = self.get("general", "log-level", "INFO").upper()
        if level not in self.VALID_LOG_LEVELS:
            logger.warning(f"Invalid log level '{level}', using INFO")
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
