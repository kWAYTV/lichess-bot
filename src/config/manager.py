"""Configuration Manager - Singleton pattern for config handling"""

import configparser
import os
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from ..utils.helpers import get_stockfish_path


class ConfigManager:
    """Singleton configuration manager for the chess bot with hot-reload support"""

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config = configparser.ConfigParser()
            self._config_path = "config.ini"
            self._last_mtime: float = 0
            self._change_callbacks: List[Callable[[Dict[str, Any]], None]] = []
            self._watcher_thread: Optional[threading.Thread] = None
            self._watcher_running = False
            self._watch_interval = 2.0  # Check every 2 seconds
            
            self._load_or_create_config()
            self._update_mtime()
            self._start_watcher()
            ConfigManager._initialized = True

    def _load_or_create_config(self) -> None:
        """Load existing config or create default one"""
        if os.path.isfile(self._config_path):
            self.config.read(self._config_path)
            logger.debug("Loaded existing config.ini")
        else:
            logger.debug("No config.ini found, creating default config")
            self._create_default_config()
            self.config.read(self._config_path)

    def _create_default_config(self) -> None:
        """Create default configuration file"""
        self.config["engine"] = {
            "path": get_stockfish_path(),
            "depth": "5",
            "hash": "2048",
            "skill-level": "14",
        }
        self.config["lichess"] = {
            "username": "user",
            "password": "pass",
            "totp-secret": "",
        }
        self.config["general"] = {
            "move-key": "end",
            "arrow": "true",
            "auto-play": "true",
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

        with open(self._config_path, "w") as configfile:
            self.config.write(configfile)

    def get(self, section: str, key: str, fallback: Any = None) -> Any:
        """Get configuration value with fallback"""
        try:
            return self.config[section].get(key, fallback)
        except KeyError:
            logger.warning(f"Section '{section}' not found in config")
            return fallback

    def get_with_aliases(self, section: str, keys: List[str], fallback: Any = None) -> Any:
        """Get configuration value trying multiple key aliases (for backward compat)
        
        Args:
            section: Config section name
            keys: List of keys to try in order (e.g., ["skill-level", "skill level", "Skill Level"])
            fallback: Value to return if none of the keys are found
        """
        try:
            section_data = self.config[section]
            for key in keys:
                if key in section_data:
                    return section_data[key]
            return fallback
        except KeyError:
            return fallback

    def get_section(self, section: str) -> Dict[str, str]:
        """Get entire configuration section"""
        try:
            return dict(self.config[section])
        except KeyError:
            logger.warning(f"Section '{section}' not found in config")
            return {}

    def set(self, section: str, key: str, value: str) -> None:
        """Set configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def save(self) -> None:
        """Save configuration to file"""
        with open(self._config_path, "w") as configfile:
            self.config.write(configfile)

    @property
    def engine_config(self) -> Dict[str, str]:
        """Get engine configuration"""
        return self.get_section("engine")

    @property
    def lichess_config(self) -> Dict[str, str]:
        """Get Lichess configuration"""
        return self.get_section("lichess")

    @property
    def general_config(self) -> Dict[str, str]:
        """Get general configuration"""
        return self.get_section("general")

    @property
    def is_autoplay_enabled(self) -> bool:
        """Check if autoplay is enabled"""
        # Check both new hyphenated and old mixed case for backward compatibility
        value = self.get(
            "general", "auto-play", self.get("general", "AutoPlay", "false")
        )
        return value.lower() == "true"

    @property
    def move_key(self) -> str:
        """Get the move key"""
        # Check both new hyphenated and old mixed case for backward compatibility
        return self.get("general", "move-key", self.get("general", "MoveKey", "end"))

    @property
    def show_arrow(self) -> bool:
        """Check if arrow should be shown"""
        # Check both new hyphenated and old mixed case for backward compatibility
        value = self.get("general", "arrow", self.get("general", "Arrow", "true"))
        return value.lower() == "true"

    @property
    def totp_secret(self) -> str:
        """Get the TOTP secret"""
        return self.get("lichess", "totp-secret", "")

    @property
    def humanization_config(self) -> Dict[str, str]:
        """Get humanization configuration"""
        return self.get_section("humanization")

    @property
    def browser_config(self) -> Dict[str, str]:
        """Get browser configuration"""
        return self.get_section("browser")

    @property
    def firefox_binary_path(self) -> str:
        """Get the Firefox binary path"""
        return self.get("browser", "firefox-binary-path", "")

    @property
    def log_level(self) -> str:
        """Get the log level"""
        level = self.get("general", "log-level", "INFO").upper()
        # Validate log level
        valid_levels = [
            "TRACE",
            "DEBUG",
            "INFO",
            "SUCCESS",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]
        if level not in valid_levels:
            logger.warning(f"Invalid log level '{level}', using INFO")
            return "INFO"
        return level

    @property
    def is_gui_enabled(self) -> bool:
        """Check if GUI is enabled (vs headless mode)"""
        value = self.get("general", "gui-enabled", "true")
        return value.lower() == "true"

    def get_humanization_delay(self, delay_type: str) -> tuple[float, float]:
        """Get min/max delays for humanization"""
        config = self.humanization_config
        if delay_type == "base":
            min_delay = float(config.get("min-delay", "0.3"))
            max_delay = float(config.get("max-delay", "1.8"))
        elif delay_type == "moving":
            min_delay = float(config.get("moving-min-delay", "0.5"))
            max_delay = float(config.get("moving-max-delay", "2.5"))
        elif delay_type == "thinking":
            min_delay = float(config.get("thinking-min-delay", "0.8"))
            max_delay = float(config.get("thinking-max-delay", "3.0"))
        else:
            # Default to base delays
            min_delay = float(config.get("min-delay", "0.3"))
            max_delay = float(config.get("max-delay", "1.8"))

        return min_delay, max_delay

    # --- Hot Reload Methods ---

    def _update_mtime(self) -> None:
        """Update the stored modification time"""
        try:
            if os.path.isfile(self._config_path):
                self._last_mtime = os.path.getmtime(self._config_path)
        except OSError:
            pass

    def _has_config_changed(self) -> bool:
        """Check if config file has been modified"""
        try:
            if os.path.isfile(self._config_path):
                current_mtime = os.path.getmtime(self._config_path)
                return current_mtime > self._last_mtime
        except OSError:
            pass
        return False

    def _start_watcher(self) -> None:
        """Start the background config file watcher"""
        if self._watcher_thread is not None:
            return

        self._watcher_running = True
        self._watcher_thread = threading.Thread(
            target=self._watch_config_file,
            daemon=True,
            name="ConfigWatcher"
        )
        self._watcher_thread.start()
        logger.debug("Config file watcher started")

    def _stop_watcher(self) -> None:
        """Stop the background config file watcher"""
        self._watcher_running = False
        if self._watcher_thread:
            self._watcher_thread.join(timeout=3.0)
            self._watcher_thread = None
            logger.debug("Config file watcher stopped")

    def _watch_config_file(self) -> None:
        """Background thread that watches for config file changes"""
        while self._watcher_running:
            try:
                if self._has_config_changed():
                    logger.info("Config file changed, reloading...")
                    old_config = self._get_config_snapshot()
                    self.reload()
                    new_config = self._get_config_snapshot()
                    self._notify_changes(old_config, new_config)
            except Exception as e:
                logger.error(f"Error in config watcher: {e}")
            
            time.sleep(self._watch_interval)

    def _get_config_snapshot(self) -> Dict[str, Dict[str, str]]:
        """Get a snapshot of current config for comparison"""
        snapshot = {}
        for section in self.config.sections():
            snapshot[section] = dict(self.config[section])
        return snapshot

    def reload(self) -> bool:
        """Reload configuration from file"""
        try:
            if os.path.isfile(self._config_path):
                self.config.read(self._config_path)
                self._update_mtime()
                logger.success("Configuration reloaded successfully")
                return True
            else:
                logger.warning("Config file not found during reload")
                return False
        except Exception as e:
            logger.error(f"Failed to reload config: {e}")
            return False

    def register_change_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Register a callback to be notified when config changes
        
        Callback receives dict with:
        - 'changed_sections': list of section names that changed
        - 'old_config': previous config snapshot
        - 'new_config': new config snapshot
        """
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
            logger.debug(f"Registered config change callback: {callback.__name__}")

    def unregister_change_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Unregister a config change callback"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            logger.debug(f"Unregistered config change callback: {callback.__name__}")

    def _notify_changes(self, old_config: Dict, new_config: Dict) -> None:
        """Notify all registered callbacks of config changes"""
        # Find what changed
        changed_sections = []
        all_sections = set(old_config.keys()) | set(new_config.keys())
        
        for section in all_sections:
            old_section = old_config.get(section, {})
            new_section = new_config.get(section, {})
            if old_section != new_section:
                changed_sections.append(section)
                # Log specific changes
                for key in set(old_section.keys()) | set(new_section.keys()):
                    old_val = old_section.get(key)
                    new_val = new_section.get(key)
                    if old_val != new_val:
                        logger.info(f"Config [{section}] {key}: {old_val} → {new_val}")

        if not changed_sections:
            return

        change_data = {
            "changed_sections": changed_sections,
            "old_config": old_config,
            "new_config": new_config,
        }

        for callback in self._change_callbacks:
            try:
                callback(change_data)
            except Exception as e:
                logger.error(f"Config change callback error: {e}")
