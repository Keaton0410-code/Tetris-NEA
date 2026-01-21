import random
import json
import numpy as np

from settings import FIELD_W, FIELD_H
from TetrisGame import Tetris
from ai_config import AI_CONFIG

# Board extraction
def get_column_heights(board):
    #Return height of blocks in each column from the bottom up
    column_heights = [0] * FIELD_W
    for x in range(FIELD_W):
        for y in range(FIELD_H):
            if board[y][x] != 0:
                column_heights[x] = FIELD_H - y
                break
    return column_heights

def count_holes(board, column_heights):
    #Count empty cells beneath the top most block in each column
    holes = 0
    for x in range(FIELD_W):
        top_filled_y = FIELD_H - column_heights[x]
        for y in range(top_filled_y, FIELD_H):
            if board[y][x] == 0:
                holes += 1
    return holes

def count_complete_lines(board):
   #Count fully filled rows
    return sum(1 for y in range(FIELD_H) if all(board[y][x] != 0 for x in range(FIELD_W)))

def count_column_transitions(board):
    #Count changes between empty and filled when scanning down columns
    transitions = 0
    for x in range(FIELD_W):
        previous_filled = 1  #treats "above the board" as filled
        for y in range(FIELD_H):
            current_filled = 1 if board[y][x] != 0 else 0
            if current_filled != previous_filled:
                transitions += 1
            previous_filled = current_filled
    return transitions

def count_row_transitions(board):
    #Count changes between empty and filled when scanning across rows
    transitions = 0
    for y in range(FIELD_H):
        previous_filled = 1  #treat "left of the board" as filled
        for x in range(FIELD_W):
            current_filled = 1 if board[y][x] != 0 else 0
            if current_filled != previous_filled:
                transitions += 1
            previous_filled = current_filled
    return transitions

def count_wells(column_heights):
   #well is a column lower than both neighbours; score by depth
    wells = 0
    for x in range(FIELD_W):
        left_height = column_heights[x - 1] if x > 0 else FIELD_H
        right_height = column_heights[x + 1] if x < FIELD_W - 1 else FIELD_H
        current_height = column_heights[x]
        if current_height < left_height and current_height < right_height:
            wells += min(left_height, right_height) - current_height
    return wells

def bumpiness(column_heights):
    #Sum of height differences between adjacent columns
    return sum(abs(column_heights[i] - column_heights[i + 1]) for i in range(FIELD_W - 1))

def aggregate_height(column_heights):
    return sum(column_heights)

def max_height(column_heights):
    return max(column_heights) if column_heights else 0

def holes_under_block(board):
    #Count holes/gaps in board that occur after the first block is seen in each column
    holes = 0
    for x in range(FIELD_W):
        seen_block = False
        for y in range(FIELD_H):
            if board[y][x] != 0:
                seen_block = True
            elif seen_block:
                holes += 1
    return holes

def extract_features(board):
    #Convert board state to a numeric feature vector. Returns a NumPy array so the neural net can process it better.
    column_heights = get_column_heights(board)
    highest_column = max_height(column_heights)

    feature_vector = np.array([
        float(aggregate_height(column_heights)),
        float(highest_column),
        float(bumpiness(column_heights)),
        float(count_holes(board, column_heights)),
        float(holes_under_block(board)),
        float(count_complete_lines(board)),
        float(count_wells(column_heights)),
        float(np.var(column_heights)),
        float(np.mean(column_heights)),
        float(count_column_transitions(board)),
        float(count_row_transitions(board)),
        float(sum(1 for h in column_heights if h == 0)),
        float(sum(1 for h in column_heights if h > FIELD_H * 0.5)),
        float(sum(1 for h in column_heights if h == highest_column)),
        float(np.std(column_heights)),
        float(sum(1 for y in range(FIELD_H) for x in range(FIELD_W) if board[y][x] != 0)),], dtype=float)

    return feature_vector


# Neural network genome

class NeuralNet:
    #1-hidden-layer neural network stored as a genome:
    def __init__(self, n_inputs=None, n_hidden=None, n_outputs=None, genes=None):
        self.input_count = n_inputs if n_inputs is not None else AI_CONFIG["n_inputs"]
        self.hidden_count = n_hidden if n_hidden is not None else AI_CONFIG["n_hidden"]
        self.output_count = n_outputs if n_outputs is not None else AI_CONFIG["n_outputs"]

        #Parameter sizes inside the genome
        self.input_to_hidden_weights_count = self.input_count * self.hidden_count
        self.hidden_bias_count = self.hidden_count
        self.hidden_to_output_weights_count = self.hidden_count * self.output_count
        self.output_bias_count = self.output_count

        self.genome_length = (self.input_to_hidden_weights_count + self.hidden_bias_count + self.hidden_to_output_weights_count + self.output_bias_count)

        if genes is None:
            self.genes = np.random.uniform(-1, 1, self.genome_length)
        else:
            self.genes = np.array(genes, dtype=float)
        self.decode_genome_to_parameters()

    def decode_genome_to_parameters(self):
        #decodes the genes into network parameters, weights and biases (W and b)
        genome = self.genes
        index = 0

        #Input to Hidden weights
        end = index + self.input_to_hidden_weights_count
        self.input_to_hidden_weights = genome[index:end].reshape(self.input_count, self.hidden_count)
        index = end

        #Hidden biases
        end = index + self.hidden_bias_count
        self.hidden_biases = genome[index:end].reshape(1, self.hidden_count)
        index = end

        #Hidden to Output weights
        end = index + self.hidden_to_output_weights_count
        self.hidden_to_output_weights = genome[index:end].reshape(self.hidden_count, self.output_count)
        index = end

        #Output biases
        end = index + self.output_bias_count
        self.output_biases = genome[index:end].reshape(1, self.output_count)

    def forward(self, feature_vector):
        #Return the network's score for a feature vector
        x = np.array(feature_vector, dtype=float).reshape(1, self.input_count)
        hidden_activations = np.tanh(x @ self.input_to_hidden_weights + self.hidden_biases)
        output_activations = hidden_activations @ self.hidden_to_output_weights + self.output_biases
        return float(output_activations.flatten()[0])

    def evaluate(self, features):
        return self.forward(features)



# Agent uses the neural network to choose moves
class NeuralNetAgent:
    def __init__(self, neural_network):
        self.neural_network = neural_network

    def choose_move(self, game: Tetris):
        possible_moves = game.get_possible_moves()
        if not possible_moves:
            print("No possible moves!")
            return None

        best_move = None
        best_score = float("-inf")

        for candidate_move in possible_moves:
            simulation_game = game.clone()
            simulation_game.apply_ai_move(candidate_move)

            simulated_board = simulation_game.get_board_matrix()
            feature_vector = extract_features(simulated_board)
            move_score = self.neural_network.evaluate(feature_vector)
            if move_score > best_score:
                best_score = move_score
                best_move = candidate_move
        return best_move

# Genetic Algorithm for training
LINES_WEIGHT = 500.0
SCORE_WEIGHT = 0.1
TOURNAMENT_SIZE = 3

class GeneticAlgorithm:
    def __init__(self, population_size, game_factory, mutation_rate=0.05, crossover_rate=0.7, evaluation_seeds=None, max_moves_per_game=700):
        self.population_size = population_size
        self.game_factory = game_factory
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.evaluation_seeds = list(evaluation_seeds) if evaluation_seeds is not None else [0]
        self.max_moves_per_game = max_moves_per_game

        self.genome_length = NeuralNet().genome_length

        self.population = [NeuralNet().genes for _ in range(population_size)]
        self.best_genes = None
        self.best_fitness = float("-inf")

    def run_game(self, genome, seed=0):
        random.seed(seed)
        np.random.seed(seed)

        neural_network = NeuralNet(genes=genome)
        agent = NeuralNetAgent(neural_network)
        game = self.game_factory()

        moves_made = 0
        while not getattr(game, "game_over_flag", False) and moves_made < self.max_moves_per_game:
            chosen_move = agent.choose_move(game)
            if chosen_move is None:
                break
            game.apply_ai_move(chosen_move)
            moves_made += 1

        lines_cleared = getattr(game, "lines_cleared", 0)
        score = getattr(game, "score", 0)
        return lines_cleared, score

    def fitness(self, genome):
        #Average fitness across fixed seeds to reduce randomness
        total_fitness = 0.0
        for seed in self.evaluation_seeds:
            lines_cleared, score = self.run_game(genome, seed=seed)
            total_fitness += (lines_cleared * LINES_WEIGHT) + (score * SCORE_WEIGHT)
        return total_fitness / float(len(self.evaluation_seeds))

    def tournament_selection(self, fitnesses):
        #Chooses one genome using tournament selection
        best_index = None
        for _ in range(TOURNAMENT_SIZE):
            candidate_index = random.randrange(self.population_size)
            if best_index is None or fitnesses[candidate_index] > fitnesses[best_index]:
                best_index = candidate_index
        return self.population[best_index].copy()

    def crossover(self, parent_a_genome, parent_b_genome):
        #Single point crossover
        if random.random() > self.crossover_rate:
            return parent_a_genome.copy(), parent_b_genome.copy()
        crossover_point = random.randint(1, self.genome_length - 1)

        child_a_genome = np.concatenate([parent_a_genome[:crossover_point], parent_b_genome[crossover_point:]])
        child_b_genome = np.concatenate([parent_b_genome[:crossover_point], parent_a_genome[crossover_point:]])
        return child_a_genome, child_b_genome

    def mutate(self, genome):
        #Mutate genome values with Gaussian noise
        for i in range(self.genome_length):
            if random.random() < self.mutation_rate:
                genome[i] += np.random.normal(0, 0.1)
        return genome

    def get_index_of_best_fitness(self, fitnesses):
        #Return index of highest fitness value 
        best_index = 0
        best_value = fitnesses[0]
        for i in range(1, len(fitnesses)):
            if fitnesses[i] > best_value:
                best_value = fitnesses[i]
                best_index = i
        return best_index

    def get_indices_sorted_by_fitness_descending(self, fitnesses):
        #Return indices sorted by fitness high to low (no lambda)
        indices = list(range(len(fitnesses)))

        for i in range(len(indices)):
            best_pos = i
            for j in range(i + 1, len(indices)):
                if fitnesses[indices[j]] > fitnesses[indices[best_pos]]:
                    best_pos = j
            indices[i], indices[best_pos] = indices[best_pos], indices[i]
        return indices

    def evolve_one_generation(self):
        fitnesses = [self.fitness(genome) for genome in self.population]

        #Update global best (no lambda)
        best_index = self.get_index_of_best_fitness(fitnesses)
        if fitnesses[best_index] > self.best_fitness:
            self.best_fitness = fitnesses[best_index]
            self.best_genes = self.population[best_index].copy()

        #Elitism: used to keep only the top 10%
        elite_count = max(1, self.population_size // 10)
        sorted_indices = self.get_indices_sorted_by_fitness_descending(fitnesses)

        new_population = []
        for i in sorted_indices[:elite_count]:
            new_population.append(self.population[i].copy())

        #Fill the rest with offspring(s)
        while len(new_population) < self.population_size:
            parent_a_genome = self.tournament_selection(fitnesses)
            parent_b_genome = self.tournament_selection(fitnesses)

            child_a_genome, child_b_genome = self.crossover(parent_a_genome, parent_b_genome)

            new_population.append(self.mutate(child_a_genome))
            if len(new_population) < self.population_size:
                new_population.append(self.mutate(child_b_genome))

        self.population = new_population
        return self.best_fitness

# Save / load genes (genomes)
def save_genes(path, genes):
    with open(path, "w") as file:
        json.dump(list(genes), file)

def load_genes(path):
    with open(path, "r") as file:
        return np.array(json.load(file), dtype=float)
