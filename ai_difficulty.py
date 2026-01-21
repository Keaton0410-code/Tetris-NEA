import random

from settings import FIELD_W, FIELD_H
from ai_tetris import NeuralNet, NeuralNetAgent, extract_features, load_genes
from ai_config import AI_CONFIG
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

# HARD AI – trained NN reverts to medium if genome missing/ nothing found in file
class HardAI:
    def __init__(self, genome_path=None):
        if genome_path is None:
            genome_path = AI_CONFIG["best_genome_file"]

        self.fallback_ai = MediumAI()  #fallback if genome is missing

        try:
            genome_genes = load_genes(genome_path)
            print(f"Loaded Hard AI genome from {genome_path}")

            neural_network = NeuralNet(genes=genome_genes)
            self.neural_network_agent = NeuralNetAgent(neural_network)

            self.is_ready = True

        except FileNotFoundError:
            print(f"[HardAI] Genome file '{genome_path}' not found. Revertingto Medium AI.")
            self.neural_network_agent = None
            self.is_ready = False

        except Exception as error:
            print(f"[HardAI] Error loading genome: {error}. Reverting Medium AI.")
            self.neural_network_agent = None
            self.is_ready = False

    def choose_move(self, game: Tetris):
        if not self.is_ready:
            return self.fallback_ai.choose_move(game)
        return self.neural_network_agent.choose_move(game)

# Difficulty selector
def get_ai_by_difficulty(difficulty_name: str):
    difficulty_name = difficulty_name.lower().strip()
    if difficulty_name == "easy":
        return EasyAI()
    if difficulty_name == "medium":
        return MediumAI()
    if difficulty_name == "hard":
        return HardAI()

    print(f"[AI Difficulty] Unknown difficulty '{difficulty_name}', defaulting to Medium")
    return MediumAI()
