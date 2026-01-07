"""Configuration management module"""

from .manager import ConfigManager
from .presets import (
    GamePreset,
    get_preset,
    get_all_presets,
    apply_preset,
    detect_preset_from_time,
    auto_apply_preset,
)

__all__ = [
    "ConfigManager",
    "GamePreset",
    "get_preset",
    "get_all_presets",
    "apply_preset",
    "detect_preset_from_time",
    "auto_apply_preset",
]
