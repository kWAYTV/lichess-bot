"""Chess Bot - Professional modular implementation"""

__author__ = "kWAY"

from .config.manager import ConfigManager
from .game import GameManager

__all__ = ["GameManager", "ConfigManager"]
