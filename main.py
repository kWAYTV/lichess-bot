"""Chess Bot - Main Entry Point"""

import signal
import sys

from loguru import logger

from src.config import ConfigManager
from src.game import GameManager
from src.gui.main_window import ChessBotGUI
from src.utils.helpers import clear_screen, signal_handler
from src.utils.logging import GUILogHandler


def main():
    """Main entry point for the chess bot"""
    game_manager = None
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        clear_screen()

        config = ConfigManager()
        gui_handler = GUILogHandler()

        # Setup logging
        logger.remove()
        logger.add(sys.stderr, level=config.log_level)

        try:
            logger.add(gui_handler.write, level=config.log_level, colorize=False)
        except Exception as e:
            logger.warning(f"Could not set up GUI logging: {e}")

        game_manager = GameManager()
        gui = ChessBotGUI(game_manager)
        gui_handler.set_gui(gui)

        # Log mode
        if config.is_autoplay_enabled:
            logger.info("AutoPlay MODE: Bot will make moves automatically")
        else:
            logger.info(f"Suggestion MODE: Press '{config.move_key}' to execute moves")

        gui.run()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        if game_manager:
            try:
                game_manager.cleanup()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                try:
                    if game_manager.browser_manager and game_manager.browser_manager.driver:
                            game_manager.browser_manager.driver.quit()
                except:
                    pass


if __name__ == "__main__":
    main()
