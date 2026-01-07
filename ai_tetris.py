import random
import json
import numpy as np
from settings import FIELD_W, FIELD_H
from TetrisGame import Tetris
from ai_config import AI_CONFIG  



def get_column_heights(board):
    heights = [0]*FIELD_W
    for x in range(FIELD_W):
        for y in range(FIELD_H):
            if board[y][x] != 0:
                heights[x] = FIELD_H - y
                break
    return heights


def count_holes(board, heights):
    holes = 0
    for x in range(FIELD_W):
        top = FIELD_H - heights[x]
        for y in range(top, FIELD_H):
            if board[y][x] == 0:
                holes += 1
    return holes


def count_complete_lines(board):
    return sum(1 for y in range(FIELD_H)
               if all(board[y][x] != 0 for x in range(FIELD_W)))


def column_transitions(board):
    """Every time we go 0→block or block→0 in a column."""
    transitions = 0
    for x in range(FIELD_W):
        prev = 1
        for y in range(FIELD_H):
            curr = 1 if board[y][x] != 0 else 0
            if curr != prev:
                transitions += 1
            prev = curr
    return transitions


def row_transitions(board):
 
    transitions = 0
    for y in range(FIELD_H):
        prev = 1
        for x in range(FIELD_W):
            curr = 1 if board[y][x] != 0 else 0
            if curr != prev:
                transitions += 1
            prev = curr
    return transitions


def count_wells(heights):
    wells = 0
    for x in range(FIELD_W):
        left = heights[x-1] if x > 0 else FIELD_H
        right = heights[x+1] if x < FIELD_W-1 else FIELD_H
        if heights[x] < left and heights[x] < right:
            wells += min(left, right) - heights[x]
    return wells


def bumpiness(heights):
    return sum(abs(heights[i] - heights[i+1]) for i in range(FIELD_W-1))


def aggregate_height(heights):
    return sum(heights)


def max_height(heights):
    return max(heights)


def holes_under_block(board):
    
    holes = 0
    for x in range(FIELD_W):
        block_seen = False
        for y in range(FIELD_H):
            if board[y][x] != 0:
                block_seen = True
            elif block_seen:
                holes += 1
    return holes


def extract_features(board):
    heights = get_column_heights(board)
    
    features = np.array([
        aggregate_height(heights),
        max_height(heights),
        bumpiness(heights),
        count_holes(board, heights),
        holes_under_block(board),
        count_complete_lines(board),
        count_wells(heights),
        np.var(heights),
        np.mean(heights),
        column_transitions(board),
        row_transitions(board),
        sum(1 for h in heights if h == 0),
        sum(1 for h in heights if h > FIELD_H * 0.5),
        len([h for h in heights if h == max_height(heights)]),
        np.std(heights),
        sum(1 for y in range(FIELD_H) for x in range(FIELD_W) if board[y][x] != 0)
    ], dtype=float)

    return features

class NeuralNet:
    def __init__(self, n_inputs=None, n_hidden=None, n_outputs=None, genes=None):
        self.n_inputs = n_inputs if n_inputs is not None else AI_CONFIG["n_inputs"]
        self.n_hidden = n_hidden if n_hidden is not None else AI_CONFIG["n_hidden"]
        self.n_outputs = n_outputs if n_outputs is not None else AI_CONFIG["n_outputs"]

        self.w1_size = self.n_inputs * self.n_hidden
        self.b1_size = self.n_hidden
        self.w2_size = self.n_hidden * self.n_outputs
        self.b2_size = self.n_outputs

        self.genome_length = self.w1_size + self.b1_size + self.w2_size + self.b2_size

        if genes is None:
            self.genes = np.random.uniform(-1, 1, self.genome_length)
        else:
            self.genes = np.array(genes, dtype=float)

        self.decode()


    def decode(self):
        g = self.genes
        idx = 0

        self.W1 = g[idx:idx+self.w1_size].reshape(self.n_inputs, self.n_hidden)
        idx += self.w1_size

        self.b1 = g[idx:idx+self.b1_size].reshape(1, self.n_hidden)
        idx += self.b1_size

        self.W2 = g[idx:idx+self.w2_size].reshape(self.n_hidden, self.n_outputs)
        idx += self.w2_size

        self.b2 = g[idx:idx+self.b2_size].reshape(1, self.n_outputs)

    def forward(self, x):
        x = np.array(x).reshape(1, self.n_inputs)
        h = np.tanh(x @ self.W1 + self.b1)
        out = h @ self.W2 + self.b2
        return out.flatten()[0]

    def evaluate(self, features):
        return self.forward(features)


# NN / agent

# In ai_tetris.py, in the NeuralNetAgent class:
# In the NeuralNetAgent.choose_move method, add this fix:
class NeuralNetAgent:
    def __init__(self, net):
        self.net = net

    def choose_move(self, game: Tetris):

        
        possible = game.get_possible_moves()
        if not possible:
            print("No possible moves!")
            return None

        best_move = None
        best_score = -1e9

        for move in possible:
            # Create simulation
            sim = game.clone()
            
            # Apply move to simulation
            sim.apply_ai_move(move)
            
            # Get board state
            board = sim.get_board_matrix()
            feats = extract_features(board)
            score = self.net.evaluate(feats)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

class GeneticAlgorithm:
    def __init__(self, pop_size, game_factory,
                 mutation_rate=0.05, crossover_rate=0.7,
                 eval_seeds=None, max_moves=700):
        self.pop_size = pop_size
        self.game_factory = game_factory
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.eval_seeds = eval_seeds if eval_seeds is not None else [0]
        self.max_moves = max_moves

        temp_net = NeuralNet()
        self.genome_len = temp_net.genome_length

        self.population = [NeuralNet().genes for _ in range(pop_size)]
        self.best_genes = None
        self.best_fitness = -1e9

    def run_game(self, genes, seed=0):
        # Make the game deterministic for fair comparisons
        random.seed(seed)
        np.random.seed(seed)

        net = NeuralNet(genes=genes)
        agent = NeuralNetAgent(net)
        game = self.game_factory()

        moves = 0
        while not getattr(game, "game_over_flag", False) and moves < self.max_moves:
            move = agent.choose_move(game)
            if move is None:
                break
            game.apply_ai_move(move)
            moves += 1

        lines = getattr(game, "lines_cleared", 0)
        score = getattr(game, "score", 0)
        return lines, score

    def fitness(self, genes):
        # Average fitness across multiple fixed seeds (reduces noise)
        total = 0.0
        for s in self.eval_seeds:
            lines, score = self.run_game(genes, seed=s)
            total += (lines * 500 + score * 0.1)
        return total / float(len(self.eval_seeds))


    def tournament(self, fits):
        best = None
        for _ in range(3):
            idx = random.randrange(self.pop_size)
            if best is None or fits[idx] > fits[best]:
                best = idx
        return self.population[best].copy()



    def crossover(self, p1, p2):
        if random.random() > self.crossover_rate:
            return p1.copy(), p2.copy()

        point = random.randint(1, self.genome_len-1)
        c1 = np.concatenate([p1[:point], p2[point:]])
        c2 = np.concatenate([p2[:point], p1[point:]])
        return c1, c2



    def mutate(self, genes):
        for i in range(self.genome_len):
            if random.random() < self.mutation_rate:
                genes[i] += np.random.normal(0, 0.1)
        return genes


    def evolve_one_generation(self):
        fitnesses = [self.fitness(g) for g in self.population]

        # update global best
        gen_best_idx = max(range(self.pop_size), key=lambda i: fitnesses[i])
        if fitnesses[gen_best_idx] > self.best_fitness:
            self.best_fitness = fitnesses[gen_best_idx]
            self.best_genes = self.population[gen_best_idx].copy()

        # create new population
        new_pop = []
        elite_count = max(1, self.pop_size // 10)
        sorted_idx = sorted(range(self.pop_size), key=lambda i: fitnesses[i], reverse=True)

        for i in sorted_idx[:elite_count]:
            new_pop.append(self.population[i].copy())

        # generate rest
        while len(new_pop) < self.pop_size:
            p1 = self.tournament(fitnesses)
            p2 = self.tournament(fitnesses)
            c1, c2 = self.crossover(p1, p2)
            new_pop.append(self.mutate(c1))
            if len(new_pop) < self.pop_size:
                new_pop.append(self.mutate(c2))

        self.population = new_pop
        return self.best_fitness


#Save and load genes to json

def save_genes(path, genes):
    with open(path, "w") as f:
        json.dump(list(genes), f)


def load_genes(path):
    with open(path, "r") as f:
        return np.array(json.load(f))
