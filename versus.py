import pygame as pg
import pathlib
import csv
import os

from datetime import datetime
from settings import *
from TetrisGame import Tetris
from ai_difficulty import get_ai_by_difficulty

# Leaderboard helpers
def _safe_name(name: str, max_len: int = 18) -> str:
    name = (name or "").strip()
    if not name:
        return "Player"
    #Remove characters that would break CSV 
    name = name.replace(",", " ").replace("\n", " ").replace("\r", " ")
    return name[:max_len]

def append_match_results(csv_path: str, results: list):
    """Appends one row per player to the match history CSV (creates file + header if needed)."""
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
    """Reads the history CSV and writes a sorted ranking file."""
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

# Match App
class MatchApp:
    def __init__(self, total_players=2, cpu_opponents=1, cpu_difficulty="medium", player_names=None):
        pg.init()
        pg.display.set_caption("Tetris – Versus")

        #Validate and clamp all inputs
        self.total_players = max(2, min(3, int(total_players)))
        self.cpu_opponents = max(0, min(2, int(cpu_opponents)))
        # A 2 board match can have at most 1 CPU
        if self.total_players == 2 and self.cpu_opponents > 1:
            self.cpu_opponents = 1
        self.cpu_difficulty = str(cpu_difficulty).lower().strip()
        if self.cpu_difficulty not in ("easy", "medium"):
            self.cpu_difficulty = "medium"
        # at least one human
        self.human_players = self.total_players - self.cpu_opponents
        if self.human_players < 1:
            self.human_players = 1
            self.cpu_opponents = self.total_players - self.human_players

        #Fill in any missing player names with default
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

        #Window layout calculation
        board_width  = FIELD_W * TILE_SIZE  
        board_height = FIELD_H * TILE_SIZE 

        if self.total_players == 2:
            margin_left = 100
            margin_right = 100
            gap = 100
            window_width = margin_left + board_width + gap + board_width + margin_right
        else:
            #spacing to fit three boards
            margin_left = 80
            margin_right = 80
            gap = 70
            window_width = margin_left + (board_width * 3) + (gap * 2) + margin_right
        margin_top = 80
        margin_bottom = 150
        window_height = margin_top + board_height + margin_bottom

        # Never exceed the physical screen
        window_width= min(window_width,1920)
        window_height = min(window_height, 1200)

        self.screen = pg.display.set_mode((window_width, window_height))
        self.clock  = pg.time.Clock()

        self.margin_left = margin_left
        self.margin_top = margin_top
        self.gap = gap
        self.board_width = board_width
        self.board_height= board_height

 #       print(f"Window: {window_width}x{window_height}")
#print(f"Boards: {self.total_players}")
    #    print(f"Board size: {board_width}x{board_height}")
    #    print(f"Margin left: {margin_left}, Gap: {gap}")
        # Load tile sprites
        self.images = self.load_sprites()

        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event= pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

        self.games = []
        self.is_cpu_board = []
        self.cpu_agents = []
        self.board_positions = []

        for board_index in range(self.total_players):
            board_x = margin_left + board_index * (board_width + gap)
            board_y = margin_top
            offset_x_tiles = board_x / TILE_SIZE
            offset_y_tiles = board_y / TILE_SIZE
            right_edge = board_x + board_width

            print(f"Board {board_index+1}: X={board_x}, Y={board_y}, Right={right_edge}")
            if right_edge > window_width:
                print(f"  WARNING: Board extends past window edge!")

            self.board_positions.append((board_x, board_y))

            game = Tetris(self, offset_tiles=vec(offset_x_tiles, offset_y_tiles), is_simulation=False)
            self.games.append(game)
            is_cpu = (board_index >= self.human_players)
            self.is_cpu_board.append(is_cpu)
            if is_cpu:
                self.cpu_agents.append(get_ai_by_difficulty(self.cpu_difficulty))
            else:
                self.cpu_agents.append(None)

        self.cpu_move_delay  = 20
        self.cpu_move_timers = [0] * self.total_players

        self.human_controls = [
            {"left": pg.K_a, "right": pg.K_d,"rotate": pg.K_w,"down": pg.K_s},
            {"left": pg.K_j, "right": pg.K_l,"rotate": pg.K_i, "down": pg.K_k},
            {"left": pg.K_LEFT,"right": pg.K_RIGHT,"rotate": pg.K_UP, "down": pg.K_DOWN},]

        self.match_finished = False
        self.results_saved  = False

    def load_sprites(self):
        """Loads tile PNGs falls back to coloured squares if the folder is missing."""
        sprite_dir = pathlib.Path(SPRITE_DIRECTORY_PATH)
        if not sprite_dir.exists():
            return self.make_fallback_sprites()
        sprite_files = [f for f in sprite_dir.rglob("*.png") if f.is_file()]
        if not sprite_files:
            return self.make_fallback_sprites()
        images = [pg.image.load(f).convert_alpha() for f in sprite_files]
        scaled = [pg.transform.scale(img, (TILE_SIZE, TILE_SIZE)) for img in images]
        return scaled

    def make_fallback_sprites(self):
        """Generates simple coloured squares when no sprite PNGs are available."""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),(255, 0, 255), (0, 255, 255), (255, 128, 0),]
        
        sprites = []
        for colour in colors:
            surface = pg.Surface((TILE_SIZE, TILE_SIZE))
            surface.fill(colour)
             #border so individual tiles are visible
            pg.draw.rect(surface, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surface)
        return sprites
    
    # Input
    def handle_input(self, game, action):
        if game.game_over_flag:
            return
        if action == "left":
            game.tetromino.move(direction="left")
        elif action == "right":
            game.tetromino.move(direction="right")
        elif action == "rotate":
            game.tetromino.rotate()
        elif action == "down":
            game.speed_up = True

    # CPU logic
    def update_cpu(self):
        for board_index in range(self.total_players):
            # Skip plaeyr boards
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

    def save_results(self):
        """Writes final scores to the appropriate CSV once the match ends (runs only once)."""
        if not self.match_finished or self.results_saved:
            return

        # CPU matches go to a separate file
        is_cpu_match  = self.cpu_opponents > 0
        history_file  = "Leaderboard_CPU.csv" if is_cpu_match else "Leaderboard.csv"

        results = []
        for board_index in range(self.total_players):
            results.append({
                "name":   self.player_names[board_index],
                "score":  self.games[board_index].score,
                "is_cpu": self.is_cpu_board[board_index]})

        append_match_results(history_file, results)
        build_rankings(history_file)
        self.results_saved = True

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
                    if   event.key == mapping["left"]:
                        self.handle_input(game, "left")
                    elif event.key == mapping["right"]:
                        self.handle_input(game, "right")
                    elif event.key == mapping["rotate"]:
                        self.handle_input(game, "rotate")
                    elif event.key == mapping["down"]:
                        self.handle_input(game, "down")

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
        self.update_cpu()
        for game in self.games:
            game.update()
        self.match_finished = all(game.game_over_flag for game in self.games)
        self.save_results()
        self.clock.tick(FPS)

    def draw(self):
        window_width, window_height = self.screen.get_size()
        for y in range(window_height):
            blend = y / window_height
            r = int(25 * (1 - blend) + 40 * blend)
            g = int(30 * (1 - blend) + 20 * blend)
            b = int(50 * (1 - blend) + 60 * blend)
            pg.draw.line(self.screen, (r, g, b), (0, y), (window_width, y))

        # Draw every game board
        for game in self.games:
            game.draw()
        
        self.draw_labels()
        pg.display.flip()

    def draw_labels(self):
        heading_font = pg.font.Font(None, 42)
        score_font = pg.font.Font(None, 36)
        status_font = pg.font.Font(None, 28)

        for board_index in range(self.total_players):
            name = self.player_names[board_index]
            game= self.games[board_index]
            board_x, board_y= self.board_positions[board_index]

            #name centred above the board
            name_text = heading_font.render(name, True, (255, 255, 150))
            name_rect = name_text.get_rect(centerx=board_x + self.board_width // 2, bottom=board_y - 10)
            self.screen.blit(name_text, name_rect)

            #Score centred below the board
            board_bottom = board_y + self.board_height
            score_text= score_font.render(f"Score: {game.score}", True, (150, 255, 150))
            score_rect = score_text.get_rect(centerx=board_x + self.board_width // 2, top=board_bottom + 10)
            self.screen.blit(score_text, score_rect)

            # "GAME OVER" 
            if game.game_over_flag:
                status_text = status_font.render("GAME OVER", True, (255, 100, 100))
                status_rect = status_text.get_rect(centerx=board_x + self.board_width // 2, top=board_bottom + 50)
                self.screen.blit(status_text, status_rect)

        # Big banner when every board has finished
        if self.match_finished:
            window_width, window_height = self.screen.get_size()
            big_font    = pg.font.Font(None, 64)
            finish_text = big_font.render("MATCH COMPLETE!", True, (255, 255, 100))
            finish_rect = finish_text.get_rect(center=(window_width // 2, window_height - 60))
            #Shadow
            shadow_text = big_font.render("MATCH COMPLETE!", True, (0, 0, 0))
            self.screen.blit(shadow_text,  (finish_rect.x + 3, finish_rect.y + 3))
            self.screen.blit(finish_text,  finish_rect)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()