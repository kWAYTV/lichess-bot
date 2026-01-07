"""Statistics Manager - Track game performance and analytics"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from ..utils.logging import logger


def _get_base_path() -> str:
    """Get base path for file resolution"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GameStats:
    """Statistics for a single game"""

    def __init__(self):
        self.game_id: Optional[str] = None
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.our_color: Optional[str] = None
        self.result: Optional[str] = None
        self.score: Optional[str] = None
        self.reason: Optional[str] = None
        self.total_moves: int = 0
        self.engine_evaluations: List[Dict] = []
        self.average_evaluation: Optional[float] = None
        self.best_evaluation: Optional[float] = None
        self.worst_evaluation: Optional[float] = None

    def complete_game(self, result: str, score: str, reason: str, total_moves: int):
        """Mark game as completed with results"""
        self.end_time = datetime.now()
        self.result = result
        self.score = score
        self.reason = reason
        self.total_moves = total_moves

        if self.engine_evaluations:
            scores = []
            for eval_data in self.engine_evaluations:
                if "score" in eval_data:
                    score_val = self._extract_score_value(eval_data["score"])
                    if score_val is not None:
                        scores.append(score_val)

            if scores:
                self.average_evaluation = sum(scores) / len(scores)
                self.best_evaluation = max(scores)
                self.worst_evaluation = min(scores)

    def add_evaluation(self, evaluation: Dict):
        """Add an engine evaluation for this game"""
        self.engine_evaluations.append(evaluation)

    def _extract_score_value(self, score) -> Optional[float]:
        """Extract numerical score value from chess engine score object"""
        try:
            if hasattr(score, "is_mate") and score.is_mate():
                mate_in = score.mate()
                return 1000.0 if mate_in > 0 else -1000.0

            if hasattr(score, "relative") and score.relative is not None:
                return score.relative.score(mate_score=10000) / 100.0

            if hasattr(score, "white") and score.white is not None:
                return score.white().score(mate_score=10000) / 100.0

            if hasattr(score, "score"):
                return score.score(mate_score=10000) / 100.0

        except Exception:
            pass
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "game_id": self.game_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "our_color": self.our_color,
            "result": self.result,
            "score": self.score,
            "reason": self.reason,
            "total_moves": self.total_moves,
            "average_evaluation": self.average_evaluation,
            "best_evaluation": self.best_evaluation,
            "worst_evaluation": self.worst_evaluation,
            "evaluation_count": len(self.engine_evaluations),
        }


class StatisticsManager:
    """Manager for tracking chess game statistics and performance"""

    def __init__(self, stats_file: str = "stats.json"):
        base = _get_base_path()
        self.stats_file = os.path.join(base, stats_file)
        self.current_game: Optional[GameStats] = None
        self.all_games: List[GameStats] = []
        self.session_games: List[GameStats] = []
        self.load_stats()

    def start_new_game(self, game_id: str = None, our_color: str = None) -> None:
        """Start tracking a new game"""
        if self.current_game:
            self.end_current_game("abandoned", "Game abandoned", "New game started", 0)

        self.current_game = GameStats()
        self.current_game.game_id = game_id or f"game_{int(datetime.now().timestamp())}"
        self.current_game.our_color = our_color

    def end_current_game(
        self, result: str, score: str, reason: str, total_moves: int
    ) -> None:
        """End the current game and save statistics"""
        if not self.current_game:
            return

        self.current_game.complete_game(result, score, reason, total_moves)
        self.all_games.append(self.current_game)
        self.session_games.append(self.current_game)

        self.save_stats()
        self.current_game = None

    def add_evaluation(self, evaluation: Dict) -> None:
        """Add an engine evaluation to the current game"""
        if self.current_game:
            self.current_game.add_evaluation(evaluation)

    def get_current_game_stats(self) -> Optional[Dict]:
        """Get statistics for the current game"""
        if self.current_game:
            return self.current_game.to_dict()
        return None

    def get_overall_stats(self, session_only: bool = False) -> Dict:
        """Get overall statistics across all games or session only"""
        games = self.session_games if session_only else self.all_games
        if not games:
            return self._empty_stats()

        total_games = len(games)
        wins = sum(1 for g in games if g.result == "win")
        losses = sum(1 for g in games if g.result == "loss")
        draws = sum(1 for g in games if g.result == "draw")

        win_rate = (wins / total_games * 100) if total_games > 0 else 0

        game_lengths = [g.total_moves for g in games if g.total_moves > 0]
        avg_game_length = sum(game_lengths) / len(game_lengths) if game_lengths else 0

        evaluations = [
            g.average_evaluation for g in games
            if g.average_evaluation is not None
        ]
        avg_evaluation = sum(evaluations) / len(evaluations) if evaluations else None

        return {
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(win_rate, 1),
            "average_game_length": round(avg_game_length, 1),
            "average_evaluation": round(avg_evaluation, 2) if avg_evaluation else None,
            "best_win": self._find_best_result("win", games),
            "worst_loss": self._find_best_result("loss", games),
        }

    def get_recent_games(self, limit: int = 10, session_only: bool = False) -> List[Dict]:
        """Get recent games (most recent first)"""
        games = self.session_games if session_only else self.all_games
        recent_games = sorted(games, key=lambda g: g.start_time, reverse=True)
        return [game.to_dict() for game in recent_games[:limit]]

    def _find_best_result(
        self, result_type: str, games: List[GameStats] = None
    ) -> Optional[Dict]:
        """Find the best result of a given type"""
        if games is None:
            games = self.all_games
        games = [g for g in games if g.result == result_type]
        if not games:
            return None

        if result_type == "win":
            games_with_eval = [g for g in games if g.average_evaluation is not None]
            if games_with_eval:
                best = max(games_with_eval, key=lambda g: g.average_evaluation)
                return {
                    "evaluation": round(best.average_evaluation, 2),
                    "moves": best.total_moves,
                    "date": best.start_time.isoformat(),
                }
        elif result_type == "loss":
            games_with_eval = [g for g in games if g.average_evaluation is not None]
            if games_with_eval:
                worst = min(games_with_eval, key=lambda g: g.average_evaluation)
                return {
                    "evaluation": round(worst.average_evaluation, 2),
                    "moves": worst.total_moves,
                    "date": worst.start_time.isoformat(),
                }

        return None

    def _empty_stats(self) -> Dict:
        """Return empty statistics structure"""
        return {
            "total_games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_rate": 0,
            "average_game_length": 0,
            "average_evaluation": None,
            "best_win": None,
            "worst_loss": None,
        }

    def save_stats(self) -> None:
        """Save statistics to file"""
        try:
            stats_data = {
                "games": [game.to_dict() for game in self.all_games],
                "last_updated": datetime.now().isoformat(),
            }

            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save statistics: {e}")

    def load_stats(self) -> None:
        """Load statistics from file"""
        if not os.path.exists(self.stats_file):
            return

        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                stats_data = json.load(f)

            self.all_games = []
            for game_data in stats_data.get("games", []):
                game = GameStats()
                game.game_id = game_data.get("game_id")
                game.start_time = datetime.fromisoformat(game_data["start_time"])
                if game_data.get("end_time"):
                    game.end_time = datetime.fromisoformat(game_data["end_time"])
                game.our_color = game_data.get("our_color")
                game.result = game_data.get("result")
                game.score = game_data.get("score")
                game.reason = game_data.get("reason")
                game.total_moves = game_data.get("total_moves", 0)
                game.average_evaluation = game_data.get("average_evaluation")
                game.best_evaluation = game_data.get("best_evaluation")
                game.worst_evaluation = game_data.get("worst_evaluation")

                self.all_games.append(game)

        except Exception as e:
            logger.error(f"Failed to load statistics: {e}")
            self.all_games = []

    def export_pgn(self, filename: str = "games.pgn") -> bool:
        """Export all games to PGN format"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                for game_stats in self.all_games:
                    if game_stats.end_time and game_stats.result:
                        f.write('[Event "Lichess Game"]\n')
                        date_str = game_stats.start_time.strftime("%Y.%m.%d")
                        f.write(f'[Date "{date_str}"]\n')
                        color = game_stats.our_color or "Unknown"
                        f.write(f'[White "{color}"]\n')
                        f.write('[Black "Opponent"]\n')
                        result_str = game_stats.score or "*"
                        f.write(f'[Result "{result_str}"]\n')
                        f.write(f'[PlyCount "{game_stats.total_moves * 2}"]\n')
                        f.write(f'[GameId "{game_stats.game_id}"]\n')
                        f.write('\n')
                        f.write(f'{result_str}')
                        f.write('\n\n')

            return True

        except Exception as e:
            logger.error(f"Failed to export PGN: {e}")
            return False

    def clear_stats(self) -> None:
        """Clear all statistics"""
        self.all_games = []
        self.current_game = None
        if os.path.exists(self.stats_file):
            try:
                os.remove(self.stats_file)
            except Exception as e:
                logger.error(f"Failed to delete statistics file: {e}")
