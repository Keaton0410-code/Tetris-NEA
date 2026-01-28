# versus.py  (SINGLE-FILE VERSION)
# Includes: multi-board local multiplayer + CPU opponents + CSV leaderboards (human + CPU)
# Drop this in as your versus.py and remove leaderboard.py if you were going to make one.

import pygame as pg
import pathlib
import csv
import os
from datetime import datetime

from settings import *
from TetrisGame import Tetris
from ai_difficulty import get_ai_by_difficulty


# =========================
# Leaderboard (CSV) helpers
# =========================
def _safe_name(name: str, max_len: int = 18) -> str:
    name = (name or "").strip()
    if not name:
        return "Player"
    name = name.replace(",", " ").replace("\n", " ").replace("\r", " ")
    return name[:max_len]


def append_match_results(csv_path: str, results: list):
    """
    Append match results to a CSV.

    results format:
      [
        {"name": "Player 1", "score": 1200, "is_cpu": False},
        {"name": "CPU 1", "score": 900, "is_cpu": True},
        ...
      ]
    """
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)

    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "name", "score", "is_cpu"])

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in results:
            writer.writerow([ts, _safe_name(row["name"]), int(row["score"]), bool(row["is_cpu"])])


def build_rankings(csv_path: str, out_path: str = None, limit: int = 50):
    """
    Build a rankings table (highest score first) from match history.
    Ranking is based on BEST score per name.
    """
    if out_path is None:
        base, ext = os.path.splitext(csv_path)
        out_path = base + "_rankings.csv"

    if not os.path.exists(csv_path):
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "name", "best_score"])
        return

    best = {}  # name -> best_score
    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = _safe_name(r.get("name", "Player"))
            try:
                score = int(r.get("score", 0))
            except ValueError:
                score = 0
            if name not in best or score > best[name]:
                best[name] = score

    sorted_rows = sorted(best.items(), key=lambda kv: kv[1], reverse=True)[:limit]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank", "name", "best_score"])
        for idx, (name, score) in enumerate(sorted_rows, start=1):
            w.writerow([idx, name, score])


# =========================
# Versus App (2–3 boards)
# =========================
class VersusApp:
    def __init__(self, total_players=2, cpu_opponents=1, cpu_difficulty="medium", player_names=None):
        pg.init()
        pg.display.set_caption("Tetris – Versus")

        # ----------------------------
        # Match settings / validation
        # ----------------------------
        self.total_players = int(total_players)
        if self.total_players < 2:
            self.total_players = 2
        if self.total_players > 3:
            self.total_players = 3

        self.cpu_opponents = int(cpu_opponents)
        if self.cpu_opponents < 0:
            self.cpu_opponents = 0
        if self.cpu_opponents > 2:
            self.cpu_opponents = 2
        if self.total_players == 2 and self.cpu_opponents > 1:
            self.cpu_opponents = 1

        self.cpu_difficulty = str(cpu_difficulty).lower().strip()
        if self.cpu_difficulty not in ("easy", "medium"):
            self.cpu_difficulty = "medium"

        # Human players are always first
        self.human_players = self.total_players - self.cpu_opponents
        if self.human_players < 1:
            self.human_players = 1
            self.cpu_opponents = self.total_players - self.human_players

        # Names list must match total boards
        if player_names is None:
            player_names = []
        self.player_names = list(player_names)

        default_names = ["Player 1", "Player 2", "Player 3"]
        while len(self.player_names) < self.total_players:
            idx = len(self.player_names)
            if idx < self.human_players:
                self.player_names.append(default_names[idx])
            else:
                self.player_names.append(f"CPU {idx - self.human_players + 1}")
        self.player_names = self.player_names[:self.total_players]

        # ----------------------------
        # Window sizing (tiles-based)
        # ----------------------------
        self.margin_tiles = 1
        self.gap_tiles = 4

        total_width_tiles = (self.margin_tiles * 2) + (self.total_players * FIELD_W) + ((self.total_players - 1) * self.gap_tiles)
        window_width_pixels = total_width_tiles * TILE_SIZE
        window_height_pixels = (FIELD_H * TILE_SIZE) + 170

        self.screen = pg.display.set_mode((window_width_pixels, window_height_pixels))
        self.clock = pg.time.Clock()

        # ----------------------------
        # Load sprites (shared)
        # ----------------------------
        self.images = self.load_sprites()

        # ----------------------------
        # Timers (shared)
        # ----------------------------
        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False

        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

        # ----------------------------
        # Create boards
        # ----------------------------
        self.games = []
        self.is_cpu_board = []
        self.cpu_agents = []

        for board_index in range(self.total_players):
            offset_x_tiles = self.margin_tiles + (board_index * (FIELD_W + self.gap_tiles))
            game = Tetris(self, offset_tiles=vec(offset_x_tiles, 0), is_simulation=False)
            self.games.append(game)

            is_cpu = (board_index >= self.human_players)
            self.is_cpu_board.append(is_cpu)

            if is_cpu:
                self.cpu_agents.append(get_ai_by_difficulty(self.cpu_difficulty))
            else:
                self.cpu_agents.append(None)

        # CPU pacing (per CPU board)
        self.cpu_move_delay = 20
        self.cpu_move_timers = [0 for _ in range(self.total_players)]

        # Controls mapping for up to 3 humans
        self.human_controls = [
            {"left": pg.K_a, "right": pg.K_d, "rotate": pg.K_w, "down": pg.K_s},             # Player 1
            {"left": pg.K_j, "right": pg.K_l, "rotate": pg.K_i, "down": pg.K_k},             # Player 2
            {"left": pg.K_LEFT, "right": pg.K_RIGHT, "rotate": pg.K_UP, "down": pg.K_DOWN}, # Player 3
        ]

        self.match_finished = False
        self.results_saved = False  # <- ensures we only write CSV once per match

    # ----------------------------
    # Sprites
    # ----------------------------
    def load_sprites(self):
        try:
            sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if item.is_file()]
            if not sprite_files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_sprites()

            loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
            scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]
            print(f"Loaded {len(scaled_images)} sprites for versus mode")
            return scaled_images

        except Exception as error:
            print(f"Error loading sprites: {error}")
            return self.create_default_sprites()

    def create_default_sprites(self):
        colours = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 165, 0)
        ]

        sprites = []
        for colour in colours:
            surface = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
            surface.fill(colour)
            pg.draw.rect(surface, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surface)

        print("Created default coloured sprites for versus mode")
        return sprites

    # ----------------------------
    # Human control routing
    # ----------------------------
    def apply_human_control(self, game, control_action):
        if game.game_over_flag:
            return

        if control_action == "left":
            game.tetromino.move(direction="left")
        elif control_action == "right":
            game.tetromino.move(direction="right")
        elif control_action == "rotate":
            game.tetromino.rotate()
        elif control_action == "down":
            game.speed_up = True

    # ----------------------------
    # CPU control
    # ----------------------------
    def cpu_control(self):
        for board_index in range(self.total_players):
            if not self.is_cpu_board[board_index]:
                continue

            game = self.games[board_index]
            if game.game_over_flag:
                continue

            self.cpu_move_timers[board_index] += 1
            if self.cpu_move_timers[board_index] < self.cpu_move_delay:
                continue

            self.cpu_move_timers[board_index] = 0

            agent = self.cpu_agents[board_index]
            if agent is None:
                continue

            chosen_move = agent.choose_move(game)
            if chosen_move:
                game.apply_ai_move(chosen_move)

    # ----------------------------
    # Leaderboard saving (once)
    # ----------------------------
    def save_match_results_if_needed(self):
        if not self.match_finished or self.results_saved:
            return

        # Any CPU present => CPU leaderboard
        is_cpu_match = self.cpu_opponents > 0
        history_file = "Leaderboard_CPU.csv" if is_cpu_match else "Leaderboard.csv"

        results = []
        for i in range(self.total_players):
            results.append({
                "name": self.player_names[i],
                "score": self.games[i].score,
                "is_cpu": self.is_cpu_board[i]
            })

        append_match_results(history_file, results)
        build_rankings(history_file)

        self.results_saved = True
        print(f"[Leaderboard] Saved results to {history_file}")

    # ----------------------------
    # Events / loop
    # ----------------------------
    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                raise SystemExit

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                raise SystemExit

            # Human keydown routing
            if event.type == pg.KEYDOWN:
                for human_index in range(self.human_players):
                    game = self.games[human_index]
                    if game.game_over_flag:
                        continue

                    mapping = self.human_controls[human_index]

                    if event.key == mapping["left"]:
                        self.apply_human_control(game, "left")
                    elif event.key == mapping["right"]:
                        self.apply_human_control(game, "right")
                    elif event.key == mapping["rotate"]:
                        self.apply_human_control(game, "rotate")
                    elif event.key == mapping["down"]:
                        self.apply_human_control(game, "down")

            # Optional: soft drop stops when key released (feel free to remove)
            if event.type == pg.KEYUP:
                for human_index in range(self.human_players):
                    mapping = self.human_controls[human_index]
                    if event.key == mapping["down"]:
                        self.games[human_index].speed_up = False

            if event.type == self.normal_tick_event:
                self.animation_trigger = True

            if event.type == self.fast_tick_event:
                self.fast_animation_trigger = True

    def update(self):
        # CPU decisions
        self.cpu_control()

        # Update all boards
        for game in self.games:
            game.update()

        # Match finished?
        self.match_finished = True
        for game in self.games:
            if not game.game_over_flag:
                self.match_finished = False
                break

        # Save results once when finished
        self.save_match_results_if_needed()

        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill((30, 40, 60))

        for game in self.games:
            game.draw()

        self.draw_ui()
        pg.display.flip()

    def draw_ui(self):
        heading_font = pg.font.Font(None, 36)
        body_font = pg.font.Font(None, 28)

        # Player labels + scores
        for board_index in range(self.total_players):
            name = self.player_names[board_index]
            game = self.games[board_index]

            offset_x_tiles = self.margin_tiles + (board_index * (FIELD_W + self.gap_tiles))
            board_left_x = offset_x_tiles * TILE_SIZE
            board_centre_x = board_left_x + (FIELD_W * TILE_SIZE // 2)

            label = name
            if game.game_over_flag:
                label = f"{name} - GAME OVER"

            label_surface = heading_font.render(label, True, (255, 220, 100))
            self.screen.blit(label_surface, (board_centre_x - label_surface.get_width() // 2, 10))

            score_surface = body_font.render(f"Score: {game.score}", True, (235, 235, 235))
            self.screen.blit(score_surface, (board_left_x + 10, FIELD_H * TILE_SIZE + 30))

        # Winner banner
        if self.match_finished:
            result_font = pg.font.Font(None, 52)

            scores = [g.score for g in self.games]
            best_score = max(scores)
            winners = [self.player_names[i] for i, s in enumerate(scores) if s == best_score]

            if len(winners) == 1:
                message_text = f"{winners[0]} WINS!"
                message_colour = (255, 255, 0)
            else:
                message_text = "DRAW: " + ", ".join(winners)
                message_colour = (200, 200, 200)

            result_surface = result_font.render(message_text, True, message_colour)
            self.screen.blit(
                result_surface,
                (self.screen.get_width() // 2 - result_surface.get_width() // 2,
                 FIELD_H * TILE_SIZE + 85)
            )

            hint_surface = body_font.render("Press ESC to exit", True, (255, 255, 255))
            self.screen.blit(
                hint_surface,
                (self.screen.get_width() // 2 - hint_surface.get_width() // 2,
                 FIELD_H * TILE_SIZE + 135)
            )

    def run(self):
        print("Versus Mode started")
        print(f"Boards: {self.total_players} | Human: {self.human_players} | CPU: {self.cpu_opponents} ({self.cpu_difficulty})")
        print("Player 1: W/A/S/D | Player 2: I/J/K/L | Player 3: Arrow Keys")
        print("Press ESC to exit")

        while True:
            try:
                self.check_events()
                self.update()
                self.draw()
            except SystemExit:
                break
