"""Utility helper functions"""

import os
import platform
import random
import sys
from time import sleep

from loguru import logger


def get_geckodriver_path() -> str:
    """Get the correct geckodriver path for current OS"""
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "geckodriver", "geckodriver.exe")
    return os.path.join("deps", "geckodriver", "geckodriver")


def get_stockfish_path() -> str:
    """Get the correct Stockfish path for current OS"""
    system = platform.system().lower()
    if system == "windows":
        return os.path.join("deps", "stockfish", "stockfish.exe")
    return os.path.join("deps", "stockfish", "stockfish")


def get_xpath_finder_path() -> str:
    """Get the xpath_finder extension path"""
    return os.path.join("deps", "xpath_finder.xpi")


def install_firefox_extensions(driver):
    """Install Firefox extensions after browser startup"""
    extension_path = get_xpath_finder_path()
    if os.path.exists(extension_path):
        try:
            driver.install_addon(extension_path)
        except Exception as e:
            logger.warning(f"Failed to install extension {extension_path}: {e}")


def humanized_delay(
    min_seconds: float = 0.5,
    max_seconds: float = 2.0,
    config_manager=None,
    delay_type: str = "base",
) -> None:
    """Add a humanized delay between actions with advanced jitter"""
    if config_manager:
        try:
            min_seconds, max_seconds = config_manager.get_humanization_delay(delay_type)
        except Exception:
            pass

    base_delay = random.uniform(min_seconds, max_seconds)
    jitter = random.uniform(0, 1.0)
    micro_variation = random.uniform(-0.1, 0.1)
    final_delay = max(0.1, base_delay + jitter + micro_variation)
    sleep(final_delay)


def advanced_humanized_delay(
    config_manager=None,
    delay_type: str = "base",
    remaining_time: int = None,
) -> None:
    """Advanced humanized delay with time pressure awareness"""
    if not config_manager:
        humanized_delay(0.5, 2.0)
        return

    min_seconds, max_seconds = config_manager.get_humanization_delay(delay_type)

    if remaining_time is not None and remaining_time >= 0:
        if remaining_time < 10:
            time_mult = 0.0
        elif remaining_time < 30:
            time_mult = 0.2
        elif remaining_time < 60:
            time_mult = 0.5
        elif remaining_time < 120:
            time_mult = 0.7
        else:
            time_mult = 1.0
    else:
        time_mult = 1.0

    if time_mult == 0.0:
        return

    base_delay = random.uniform(min_seconds, max_seconds) * time_mult
    jitter_1 = random.uniform(0, 0.8 * time_mult)
    jitter_2 = random.uniform(0, 0.3 * time_mult)

    pause_bonus = 0
    if time_mult >= 0.7 and random.random() < 0.1:
        pause_bonus = random.uniform(0.5, 1.5) * time_mult

    micro_hesitation = random.uniform(-0.05, 0.15) * time_mult
    final_delay = max(0.05, base_delay + jitter_1 + jitter_2 + pause_bonus + micro_hesitation)
    sleep(final_delay)


def clear_screen() -> None:
    """Clear the terminal screen on both Windows and Unix-like systems"""
    os.system("cls" if os.name == "nt" else "clear")


def signal_handler(_sig, _frame):
    """Handle graceful shutdown"""
    sys.exit(0)


def get_seconds(time_str: str) -> int:
    """Convert time string to seconds"""
    semicolons = time_str.count(":")

    if semicolons == 2:
        hh, mm, ss = time_str.split(":")
        return int(hh) * 3600 + int(mm) * 60 + int(ss)
    if semicolons == 1:
        fixed = time_str.partition(".")
        mm, ss = fixed[0].split(":")
        return int(mm) * 60 + int(ss)

    return 0
