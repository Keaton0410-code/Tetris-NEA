# versus.py - DYNAMIC SCALABLE LAYOUT VERSION
# Automatically scales boards to fit any number of players in any window size

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
    """Append match results to a CSV."""
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
    """Build a rankings table from match history."""
    if out_path is None:
        base, ext = os.path.splitext(csv_path)
        out_path = base + "_rankings.csv"

    if not os.path.exists(csv_path):
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "name", "best_score"])
        return

    best = {}
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
# DYNAMIC LAYOUT CALCULATOR
# =========================
class LayoutCalculator:
    """
    Calculates optimal layout for N boards in a window.
    Makes everything scalable and dynamic.
    """
    def __init__(self, num_boards, target_window_width=1600, target_window_height=1080):
        self.num_boards = num_boards
        self.target_width = target_window_width
        self.target_height = target_window_height
        
        # Standard Tetris board dimensions in tiles
        self.board_width_tiles = FIELD_W  # 10
        self.board_height_tiles = FIELD_H  # 20
        
        # Layout parameters (as ratios of board size)
        self.margin_ratio = 0.15  # Margins are 15% of board width
        self.gap_ratio = 0.12     # Gaps are 12% of board width
        self.top_margin_ratio = 0.1    # Top margin for labels
        self.bottom_margin_ratio = 0.15  # Bottom margin for scores
        
        # Calculate optimal tile size and layout
        self.calculate_layout()
    
    def calculate_layout(self):
        """
        Calculate tile size that fits all boards in target window.
        Works backwards from desired window size.
        """
        # Calculate how much horizontal space we need (in tiles)
        # total_width = left_margin + (n * board_width) + ((n-1) * gap) + right_margin
        
        margin_tiles = self.board_width_tiles * self.margin_ratio
        gap_tiles = self.board_width_tiles * self.gap_ratio
        
        total_horizontal_tiles = (
            margin_tiles * 2 +  # left + right margin
            self.num_boards * self.board_width_tiles +  # all boards
            (self.num_boards - 1) * gap_tiles  # gaps between boards
        )
        
        # Calculate how much vertical space we need (in tiles)
        top_margin_tiles = self.board_height_tiles * self.top_margin_ratio
        bottom_margin_tiles = self.board_height_tiles * self.bottom_margin_ratio
        
        total_vertical_tiles = (
            top_margin_tiles +
            self.board_height_tiles +
            bottom_margin_tiles
        )
        
        # Calculate tile size that fits everything
        # tile_size_from_width = target_width / total_horizontal_tiles
        # tile_size_from_height = target_height / total_vertical_tiles
        # Use the smaller to ensure everything fits
        
        tile_size_from_width = self.target_width / total_horizontal_tiles
        tile_size_from_height = self.target_height / total_vertical_tiles
        
        # Use smaller tile size to ensure fit, but keep reasonable minimum
        self.tile_size = int(min(tile_size_from_width, tile_size_from_height))
        self.tile_size = max(self.tile_size, 30)  # Minimum 30px tiles
        self.tile_size = min(self.tile_size, 60)  # Maximum 60px tiles
        
        # Now calculate actual window size with this tile size
        self.actual_width = int(total_horizontal_tiles * self.tile_size)
        self.actual_height = int(total_vertical_tiles * self.tile_size)
        
        # Calculate actual pixel dimensions for layout
        self.margin_left = int(margin_tiles * self.tile_size)
        self.margin_top = int(top_margin_tiles * self.tile_size)
        self.margin_bottom = int(bottom_margin_tiles * self.tile_size)
        self.gap_between_boards = int(gap_tiles * self.tile_size)
        
        self.board_width_pixels = self.board_width_tiles * self.tile_size
        self.board_height_pixels = self.board_height_tiles * self.tile_size
        
        print(f"Number of boards: {self.num_boards}")
        print(f"Target window: {self.target_width}×{self.target_height}")
        print(f"Calculated tile size: {self.tile_size}px")
        print(f"Actual window: {self.actual_width}×{self.actual_height}")
        print(f"Board size: {self.board_width_pixels}×{self.board_height_pixels}")
        print(f"Margins: L={self.margin_left} T={self.margin_top} B={self.margin_bottom}")
        print(f"Gap between boards: {self.gap_between_boards}")
    
    def get_board_position(self, board_index):
        """Get pixel position for a specific board."""
        x = self.margin_left + board_index * (self.board_width_pixels + self.gap_between_boards)
        y = self.margin_top
        
        print(f"Board {board_index+1}: X={x}, Y={y}, Right edge={x + self.board_width_pixels}")
        
        return (x, y)
    
    def get_window_size(self):
        """Get calculated window size."""
        return (self.actual_width, self.actual_height)


class VersusApp:
    def __init__(self, total_players=2, cpu_opponents=1, cpu_difficulty="medium", player_names=None):
        pg.init()
        pg.display.set_caption("Tetris – Versus")

        # Match settings / validation
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

   
        self.layout = LayoutCalculator(
            num_boards=self.total_players,
            target_window_width=1600,
            target_window_height=1080
        )
        
        window_size = self.layout.get_window_size()
        self.screen = pg.display.set_mode(window_size)
        self.clock = pg.time.Clock()
        
        # Store for easy access
        self.tile_size = self.layout.tile_size


        self.images = self.load_sprites()


        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False

        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)


        self.games = []
        self.is_cpu_board = []
        self.cpu_agents = []
        self.board_positions = []

        for board_index in range(self.total_players):
            # Get position from layout calculator
            board_x_pixels, board_y_pixels = self.layout.get_board_position(board_index)
            
            # Convert to tile offset (using our calculated tile size)
            offset_x_tiles = board_x_pixels / self.tile_size
            offset_y_tiles = board_y_pixels / self.tile_size
            
            # Store pixel positions for UI drawing
            self.board_positions.append((board_x_pixels, board_y_pixels))
            
            # Create game with scaled tile size
            # We need to temporarily override TILE_SIZE for this board
            game = Tetris(self, offset_tiles=vec(offset_x_tiles, offset_y_tiles), is_simulation=False)
            self.games.append(game)

            is_cpu = (board_index >= self.human_players)
            self.is_cpu_board.append(is_cpu)

            if is_cpu:
                self.cpu_agents.append(get_ai_by_difficulty(self.cpu_difficulty))
            else:
                self.cpu_agents.append(None)

        # CPU pacing
        self.cpu_move_delay = 20
        self.cpu_move_timers = [0 for _ in range(self.total_players)]

        # Controls mapping
        self.human_controls = [
            {"left": pg.K_a, "right": pg.K_d, "rotate": pg.K_w, "down": pg.K_s},
            {"left": pg.K_j, "right": pg.K_l, "rotate": pg.K_i, "down": pg.K_k},
            {"left": pg.K_LEFT, "right": pg.K_RIGHT, "rotate": pg.K_UP, "down": pg.K_DOWN},
        ]

        self.match_finished = False
        self.results_saved = False

    # ----------------------------
    # Sprites - SCALED TO TILE SIZE
    # ----------------------------
    def load_sprites(self):
        sprite_dir = pathlib.Path(SPRITE_DIRECTORY_PATH)
        if not sprite_dir.exists():
            return self.create_default_sprites()

        sprite_files = [f for f in sprite_dir.rglob("*.png") if f.is_file()]
        if not sprite_files:
            return self.create_default_sprites()

        images = [pg.image.load(f).convert_alpha() for f in sprite_files]
        # Scale to our calculated tile size
        scaled = [pg.transform.scale(img, (self.tile_size, self.tile_size)) for img in images]
        return scaled

    def create_default_sprites(self):
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (255, 128, 0),
        ]
        
        sprites = []
        for colour in colors:
            surface = pg.Surface((self.tile_size, self.tile_size))
            surface.fill(colour)
            pg.draw.rect(surface, (255, 255, 255), (0, 0, self.tile_size, self.tile_size), 2)
            sprites.append(surface)

        print(f"Created default sprites at {self.tile_size}×{self.tile_size}px")
        return sprites

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

    # CPU control
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

    # Leaderboard saving
    def save_match_results_if_needed(self):
        if not self.match_finished or self.results_saved:
            return

        is_cpu_match = self.cpu_opponents > 0
        history_file = "Leaderboard_CPU.csv" if is_cpu_match else "Leaderboard.csv"

        results = []
        for board_index in range(self.total_players):
            name = self.player_names[board_index]
            score = self.games[board_index].score
            is_cpu = self.is_cpu_board[board_index]
            results.append({"name": name, "score": score, "is_cpu": is_cpu})

        append_match_results(history_file, results)
        build_rankings(history_file)
        self.results_saved = True

    # Events
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
        self.cpu_control()

        for game in self.games:
            game.update()

        self.match_finished = True
        for game in self.games:
            if not game.game_over_flag:
                self.match_finished = False
                break

        self.save_match_results_if_needed()
        self.clock.tick(FPS)

    def draw(self):
        # Gradient background
        window_width, window_height = self.layout.get_window_size()
        for y in range(window_height):
            blend = y / window_height
            r = int(25 * (1 - blend) + 40 * blend)
            g = int(30 * (1 - blend) + 20 * blend)
            b = int(50 * (1 - blend) + 60 * blend)
            pg.draw.line(self.screen, (r, g, b), (0, y), (window_width, y))

        for game in self.games:
            game.draw()

        self.draw_ui()
        pg.display.flip()

    def draw_ui(self):
        # Scale font sizes based on tile size
        heading_size = int(self.tile_size * 0.8)
        score_size = int(self.tile_size * 0.7)
        status_size = int(self.tile_size * 0.5)
        
        heading_font = pg.font.Font(None, heading_size)
        score_font = pg.font.Font(None, score_size)
        status_font = pg.font.Font(None, status_size)

        for board_index in range(self.total_players):
            name = self.player_names[board_index]
            game = self.games[board_index]
            board_x, board_y = self.board_positions[board_index]
            
            board_width = self.layout.board_width_pixels

            # Player name above board
            name_text = heading_font.render(name, True, (255, 255, 150))
            name_rect = name_text.get_rect(centerx=board_x + board_width // 2, bottom=board_y - 10)
            self.screen.blit(name_text, name_rect)

            # Score below board
            board_bottom = board_y + self.layout.board_height_pixels
            score_text = score_font.render(f"Score: {game.score}", True, (150, 255, 150))
            score_rect = score_text.get_rect(centerx=board_x + board_width // 2, top=board_bottom + 10)
            self.screen.blit(score_text, score_rect)

            # Game over status
            if game.game_over_flag:
                status_text = status_font.render("GAME OVER", True, (255, 100, 100))
                status_rect = status_text.get_rect(centerx=board_x + board_width // 2, top=board_bottom + 45)
                self.screen.blit(status_text, status_rect)

        # Match finished message
        if self.match_finished:
            window_width, window_height = self.layout.get_window_size()
            big_font = pg.font.Font(None, int(self.tile_size * 1.2))
            finish_text = big_font.render("MATCH COMPLETE!", True, (255, 255, 100))
            finish_rect = finish_text.get_rect(center=(window_width // 2, window_height - 60))
            
            shadow_text = big_font.render("MATCH COMPLETE!", True, (0, 0, 0))
            self.screen.blit(shadow_text, (finish_rect.x + 3, finish_rect.y + 3))
            self.screen.blit(finish_text, finish_rect)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()