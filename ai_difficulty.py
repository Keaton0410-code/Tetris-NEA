import random

from settings import FIELD_W, FIELD_H
from TetrisGame import Tetris

# EASY AI – random move
class EasyAI:
    def choose_move(self, game: Tetris):
        possible_moves = game.get_possible_moves()
        return random.choice(possible_moves) if possible_moves else None

# MEDIUM AI – heuristic (no training)
HEURISTIC_WEIGHTS = {"aggregate_height": -0.510066, "complete_lines": 0.760666, "holes": -0.35663, "bumpiness": -0.184483}

class MediumAI:
    def choose_move(self, game: Tetris):
        possible_moves = game.get_possible_moves()
        if not possible_moves:
            return None

        best_move = None
        best_score = -1e9

        for candidate_move in possible_moves:
            simulation_game = game.clone()
            simulation_game.apply_ai_move(candidate_move)

            simulated_board = simulation_game.get_board_matrix()
            feature_vector = extract_features(simulated_board)

            #Feature indices according to extract_features in ai_tetris.py
            aggregate_height_value = feature_vector[0]
            bumpiness_value = feature_vector[2]
            holes_value = feature_vector[3]
            complete_lines_value = feature_vector[5]

            score = (
                HEURISTIC_WEIGHTS["aggregate_height"] * aggregate_height_value +
                HEURISTIC_WEIGHTS["complete_lines"] * complete_lines_value +
                HEURISTIC_WEIGHTS["holes"] * holes_value +
                HEURISTIC_WEIGHTS["bumpiness"] * bumpiness_value)

            if score > best_score:
                best_score = score
                best_move = candidate_move
        return best_move


# Difficulty selector
def get_ai_by_difficulty(difficulty_name: str):
    difficulty_name = difficulty_name.lower().strip()
    if difficulty_name == "easy":
        return EasyAI()
    if difficulty_name == "medium":
        return MediumAI()

    print(f"[AI Difficulty] Unknown difficulty '{difficulty_name}', defaulting to Medium")
    return MediumAI()
