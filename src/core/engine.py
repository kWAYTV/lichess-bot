"""Chess Engine - Stockfish integration"""

from typing import Any, Dict, Optional

import chess
import chess.engine
from loguru import logger

from ..config import ConfigManager
from ..utils.resilience import retry_on_exception, safe_execute


class ChessEngine:
    """Chess engine wrapper for Stockfish"""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._current_skill_level: int = 0
        self._current_hash_size: int = 0
        self._initialize_engine()
        
        # Register for config changes
        self.config_manager.register_change_callback(self._on_config_change)

    def _initialize_engine(self) -> None:
        """Initialize the chess engine"""
        try:
            engine_path = self.config_manager.get_with_aliases("engine", ["path", "Path"], "")

            if not engine_path:
                raise ValueError("Engine path not found in config")

            self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
            logger.debug(f"Started chess engine: {engine_path}")

            # Configure engine options
            skill_level = int(self.config_manager.get_with_aliases(
                "engine", ["skill-level", "skill level", "Skill Level"], 14
            ))
            hash_size = int(self.config_manager.get_with_aliases(
                "engine", ["hash", "Hash"], 2048
            ))

            options = {
                "Skill Level": skill_level,
                "Hash": hash_size,
            }

            self.engine.configure(options)
            self._current_skill_level = skill_level
            self._current_hash_size = hash_size
            logger.debug(
                f"Engine configured - Skill: {options['Skill Level']}, Hash: {options['Hash']}"
            )

        except Exception as e:
            logger.error(f"Failed to start chess engine: {e}")
            raise

    @retry_on_exception(
        max_retries=3,
        delay=1.0,
        exceptions=(chess.engine.EngineError, chess.engine.EngineTerminatedError),
    )
    def get_best_move(
        self, board: chess.Board, depth: Optional[int] = None
    ) -> chess.engine.PlayResult:
        """Get the best move for the current position"""
        if not self.engine:
            logger.warning("Engine not initialized, attempting to reinitialize")
            self._initialize_engine()

        if depth is None:
            depth = int(self.config_manager.get_with_aliases(
                "engine", ["depth", "Depth"], 5
            ))

        logger.debug(f"Calculating best move (depth: {depth})")

        # Get both move and evaluation
        result = self.engine.play(
            board,
            chess.engine.Limit(depth=depth),
            game=object,
            info=chess.engine.INFO_ALL,  # Request all info including evaluation
        )

        # Get detailed analysis for evaluation
        analysis = self.engine.analyse(
            board, chess.engine.Limit(depth=depth), info=chess.engine.INFO_ALL
        )

        # Add evaluation to result
        if hasattr(result, "info"):
            result.info.update(analysis)
        else:
            result.info = analysis

        logger.debug(f"Engine suggests: {result.move}")
        return result

    @retry_on_exception(
        max_retries=2,
        delay=0.5,
        exceptions=(chess.engine.EngineError, chess.engine.EngineTerminatedError),
    )
    def analyze_position(
        self, board: chess.Board, time_limit: float = 1.0
    ) -> Dict[str, Any]:
        """Analyze the current position"""
        if not self.engine:
            logger.warning("Engine not initialized, attempting to reinitialize")
            self._initialize_engine()

        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))

        return info

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.engine is not None

    def _on_config_change(self, change_data: Dict[str, Any]) -> None:
        """Handle config file changes - reconfigure engine if needed"""
        if "engine" not in change_data.get("changed_sections", []):
            return
        
        logger.info("Engine config changed, reconfiguring...")
        self._reconfigure_engine()

    def _reconfigure_engine(self) -> None:
        """Reconfigure engine with current config values (without restart)"""
        if not self.engine:
            return

        try:
            skill_level = int(self.config_manager.get_with_aliases(
                "engine", ["skill-level", "skill level", "Skill Level"], 14
            ))
            hash_size = int(self.config_manager.get_with_aliases(
                "engine", ["hash", "Hash"], 2048
            ))

            # Only reconfigure if values changed
            if skill_level != self._current_skill_level or hash_size != self._current_hash_size:
                options = {
                    "Skill Level": skill_level,
                    "Hash": hash_size,
                }
                self.engine.configure(options)
                self._current_skill_level = skill_level
                self._current_hash_size = hash_size
                logger.success(f"Engine reconfigured - Skill: {skill_level}, Hash: {hash_size}")
            else:
                logger.debug("Engine config unchanged, skipping reconfigure")

        except Exception as e:
            logger.error(f"Failed to reconfigure engine: {e}")

    def quit(self) -> None:
        """Stop the chess engine"""
        if self.engine:
            logger.debug("Stopping chess engine")
            safe_execute(self.engine.quit, log_errors=True)
            self.engine = None
        
        # Unregister callback
        self.config_manager.unregister_change_callback(self._on_config_change)
