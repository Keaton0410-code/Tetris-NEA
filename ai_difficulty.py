import random

from TetrisGame import Tetris
from ai_features import aggregate_height, complete_lines, holes, bumpiness


HEURISTIC_WEIGHTS = {
    "aggregate_height": -0.510066,
    "complete_lines": 0.760666,
    "holes": -0.35663,
    "bumpiness": -0.184483,
}


class EasyAI:
    def choose_move(self, game: Tetris):
        possible_moves = game.get_possible_moves()
        return random.choice(possible_moves) if possible_moves else None


class MediumAI:
    def choose_move(self, game: Tetris):
        possible_moves = game.get_possible_moves()
        if not possible_moves:
            return None

        best_move = None
        best_score = -1e9

        for move in possible_moves:
            simulation = game.clone()
            simulation.apply_ai_move(move)
            board = simulation.get_board()

            score = (
                HEURISTIC_WEIGHTS["aggregate_height"] * aggregate_height(board)
                + HEURISTIC_WEIGHTS["complete_lines"] * complete_lines(board)
                + HEURISTIC_WEIGHTS["holes"] * holes(board)
                + HEURISTIC_WEIGHTS["bumpiness"] * bumpiness(board)
            )

            if score > best_score:
                best_score = score
                best_move = move

        return best_move


def get_ai_by_difficulty(difficulty_name: str):
    difficulty_key = (difficulty_name or "").lower().strip()
    if difficulty_key == "easy":
        return EasyAI()
    if difficulty_key == "medium":
        return MediumAI()

    print(f"[AI Difficulty] Unknown difficulty '{difficulty_name}', defaulting to Medium")
    return MediumAI()