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
        self.config = config_manager
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Initialize the chess engine"""
        try:
            cfg = self.config.engine_config
            path = cfg.get("path", "")

            if not path:
                raise ValueError("Engine path not found in config")

            self.engine = chess.engine.SimpleEngine.popen_uci(path)
            logger.debug(f"Started chess engine: {path}")

            skill = int(cfg.get("skill-level", 14))
            hash_size = int(cfg.get("hash", 2048))

            self.engine.configure({"Skill Level": skill, "Hash": hash_size})
            logger.debug(f"Engine configured - Skill: {skill}, Hash: {hash_size}")

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
            logger.warning("Engine not initialized, reinitializing")
            self._initialize_engine()

        if depth is None:
            depth = int(self.config.get("engine", "depth", 5))

        logger.debug(f"Calculating best move (depth: {depth})")

        result = self.engine.play(
            board,
            chess.engine.Limit(depth=depth),
            game=object,
            info=chess.engine.INFO_ALL,
        )

        analysis = self.engine.analyse(
            board, chess.engine.Limit(depth=depth), info=chess.engine.INFO_ALL
        )

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
            logger.warning("Engine not initialized, reinitializing")
            self._initialize_engine()

        return self.engine.analyse(board, chess.engine.Limit(time=time_limit))

    def is_running(self) -> bool:
        """Check if engine is running"""
        return self.engine is not None

    def quit(self) -> None:
        """Stop the chess engine"""
        if self.engine:
            logger.debug("Stopping chess engine")
            safe_execute(self.engine.quit, log_errors=True)
            self.engine = None
