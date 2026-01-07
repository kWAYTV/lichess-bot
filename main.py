"""Chess Bot - Main Entry Point"""

import signal
import sys

from src.config import ConfigManager
from src.game import GameManager
from src.gui.main_window import ChessBotGUI
from src.utils.helpers import clear_screen, signal_handler
from src.utils.logging import GUILogHandler, logger, setup_logging


def main():
    """Main entry point for the chess bot"""
    game_manager = None

    try:
        signal.signal(signal.SIGINT, signal_handler)
        clear_screen()

        config = ConfigManager()
        gui_handler = GUILogHandler()

        setup_logging(config.log_level, gui_handler)

        game_manager = GameManager()
        gui = ChessBotGUI(game_manager)
        gui_handler.set_gui(gui)

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
                except Exception:
                    pass


if __name__ == "__main__":
    main()
