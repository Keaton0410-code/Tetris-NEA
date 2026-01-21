import os
import pygame as pg
import numpy as np

from ai_tetris import GeneticAlgorithm, save_genes, load_genes, NeuralNet
from TetrisGame import Tetris
from ai_config import AI_CONFIG

def game_factory():
    class DummyApp:
        images = []    # Tetromino doesn't need this in simulation (nothing is displayed training in background essentially)
        animation_trigger = True
        fast_animation_trigger = False
    return Tetris(DummyApp(), is_simulation=True)

def seed_population_from_best(ga, best_genes, clones=8):
    """
    Put best genes into population[0] and inject mutated copies after it.
    """
    ga.population[0] = best_genes.copy()
    for i in range(1, min(clones + 1, ga.pop_size)):
        child = best_genes.copy()
        child = ga.mutate(child)
        ga.population[i] = child

def train():
    pg.init()
    print(" Training GA on 9–16–1 Network")

    ga = GeneticAlgorithm(
        pop_size=AI_CONFIG["population_size"],
        game_factory=game_factory,
        mutation_rate=AI_CONFIG["mutation_rate"],
        crossover_rate=AI_CONFIG["crossover_rate"],
        eval_seeds=AI_CONFIG["eval_seeds"],
        max_moves=AI_CONFIG["max_moves"],)

    best_path = AI_CONFIG["best_genome_file"]
    if AI_CONFIG.get("resume_from_best", False) and os.path.exists(best_path):
        best_genes = load_genes(best_path)
        ga.best_genes = best_genes.copy()
        ga.best_fitness = ga.fitness(best_genes)

        seed_population_from_best(ga, best_genes, clones=AI_CONFIG.get("seed_clones", 8))

        print(f"Resuming from {best_path}")
        print(f"Loaded best fitness: {ga.best_fitness:.2f}")
    else:
        print("Starting from scratch (no genome found).")

    generations = AI_CONFIG["generations"]

    for gen in range(generations):
        best_fit = ga.evolve_one_generation()

        #compute avg fitness for visibility (costs a bit of time)
        fits = [ga.fitness(g) for g in ga.population]
        avg_fit = sum(fits) / float(len(fits))

        print(f"Gen {gen:03d} | Best: {best_fit:.2f} | Avg: {avg_fit:.2f}")

    print("\n Training done.")
    print(f" Saving best genome → {best_path}")
    save_genes(best_path, ga.best_genes)
    print("Saved.")


if __name__ == "__main__":
    train()