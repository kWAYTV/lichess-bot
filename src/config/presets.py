"""Game Mode Presets - Pre-configured settings for different time controls"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class GamePreset:
    """Preset configuration for a game mode"""
    name: str
    depth: int
    skill_level: int
    min_delay: float
    max_delay: float
    moving_min: float
    moving_max: float
    thinking_min: float
    thinking_max: float
    description: str


PRESETS: Dict[str, GamePreset] = {
    "bullet": GamePreset(
        name="Bullet",
        depth=6,
        skill_level=17,
        min_delay=0.1,
        max_delay=0.3,
        moving_min=0.1,
        moving_max=0.3,
        thinking_min=0.2,
        thinking_max=0.5,
        description="1+0, 2+1 - Fast moves, minimal thinking",
    ),
    "blitz": GamePreset(
        name="Blitz",
        depth=10,
        skill_level=18,
        min_delay=0.2,
        max_delay=0.5,
        moving_min=0.2,
        moving_max=0.5,
        thinking_min=0.4,
        thinking_max=1.0,
        description="3+0, 3+2, 5+0, 5+3 - Balanced speed",
    ),
    "rapid": GamePreset(
        name="Rapid",
        depth=14,
        skill_level=19,
        min_delay=0.4,
        max_delay=1.0,
        moving_min=0.4,
        moving_max=1.2,
        thinking_min=0.8,
        thinking_max=2.0,
        description="10+0, 10+5, 15+10 - More time to think",
    ),
    "classical": GamePreset(
        name="Classical",
        depth=18,
        skill_level=20,
        min_delay=0.8,
        max_delay=2.0,
        moving_min=0.8,
        moving_max=2.5,
        thinking_min=1.5,
        thinking_max=4.0,
        description="30+0, 30+20 - Maximum strength",
    ),
}


def get_preset(name: str) -> GamePreset:
    """Get preset by name (case-insensitive)"""
    return PRESETS.get(name.lower())


def get_all_presets() -> Dict[str, GamePreset]:
    """Get all available presets"""
    return PRESETS


def apply_preset(config_manager, preset_name: str) -> bool:
    """Apply a preset to the config manager"""
    preset = get_preset(preset_name)
    if not preset:
        return False

    config_manager.set("engine", "depth", str(preset.depth))
    config_manager.set("engine", "skill-level", str(preset.skill_level))

    config_manager.set("humanization", "min-delay", str(preset.min_delay))
    config_manager.set("humanization", "max-delay", str(preset.max_delay))
    config_manager.set("humanization", "moving-min-delay", str(preset.moving_min))
    config_manager.set("humanization", "moving-max-delay", str(preset.moving_max))
    config_manager.set("humanization", "thinking-min-delay", str(preset.thinking_min))
    config_manager.set("humanization", "thinking-max-delay", str(preset.thinking_max))

    config_manager.save()
    return True


def detect_preset_from_time(initial_seconds: int) -> str:
    """Detect which preset to use based on initial clock time in seconds"""
    if initial_seconds <= 120:
        return "bullet"
    if initial_seconds <= 300:
        return "blitz"
    if initial_seconds <= 900:
        return "rapid"
    return "classical"


def auto_apply_preset(config_manager, initial_seconds: int) -> str:
    """Detect and apply the appropriate preset based on clock time"""
    preset_name = detect_preset_from_time(initial_seconds)
    apply_preset(config_manager, preset_name)
    return preset_name
