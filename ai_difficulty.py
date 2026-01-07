import random
from settings import FIELD_W, FIELD_H
from ai_tetris import NeuralNet, NeuralNetAgent, extract_features, load_genes
from ai_config import AI_CONFIG

from TetrisGame import Tetris

# EASY AI – random move

class EasyAI:
    def choose_move(self, game: Tetris):
        moves = game.get_possible_moves()
        return random.choice(moves) if moves else None



# MEDIUM AI –  heuristic (no training)

HEURISTIC_WEIGHTS = {
    "aggregate_height": -0.510066,
    "complete_lines":    0.760666,
    "holes":            -0.35663,
    "bumpiness":        -0.184483,
}

class MediumAI:
    def choose_move(self, game: Tetris):
        moves = game.get_possible_moves()
        if not moves:
            return None

        best_move = None
        best_score = -1e9

        for move in moves:
            sim = game.clone()
            sim.apply_ai_move(move)
            board = sim.get_board_matrix()
            feats = extract_features(board)

            # feature indices according to your extract_features:
            agg_height = feats[0]
            bump       = feats[2]
            holes      = feats[3]
            comp_lines = feats[5]

            score = (
                HEURISTIC_WEIGHTS["aggregate_height"] * agg_height +
                HEURISTIC_WEIGHTS["complete_lines"]    * comp_lines +
                HEURISTIC_WEIGHTS["holes"]             * holes +
                HEURISTIC_WEIGHTS["bumpiness"]         * bump
            )

            if score > best_score:
                best_score = score
                best_move = move

        return best_move



# HARD AI – GA-trained Neural Net (falls back if missing)

class HardAI:
    def __init__(self, genome_path=None):
        if genome_path is None:
            genome_path = AI_CONFIG["best_genome_file"]

        self._fallback = MediumAI()  # fallback if genome missing

        try:
            genes = load_genes(genome_path)
            print(f"Loaded hard AI genome from {genome_path}")
            self.nn = NeuralNet(genes=genes)
            self.agent = NeuralNetAgent(self.nn)
            self.valid = True
        except FileNotFoundError:
            print(f"[HardAI] Genome file '{genome_path}' not found. Falling back to Medium AI.")
            self.nn = None
            self.agent = None
            self.valid = False
        except Exception as e:
            print(f"[HardAI] Error loading genome: {e}. Falling back to Medium AI.")
            self.nn = None
            self.agent = None
            self.valid = False

    def choose_move(self, game: Tetris):
        if not self.valid:
            return self._fallback.choose_move(game)
        return self.agent.choose_move(game)

# Difficulty selector

def get_ai_by_difficulty(name: str):
    name = name.lower().strip()

    if name == "easy":
        return EasyAI()
    if name == "medium":
        return MediumAI()
    if name == "hard":
        return HardAI()

    print(f"[AI Difficulty] Unknown '{name}', defaulting to MEDIUM")
    return MediumAI()
