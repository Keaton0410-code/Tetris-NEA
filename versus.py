import pygame as pg
import pathlib

from settings import *
from TetrisGame import Tetris
from ai_difficulty import get_ai_by_difficulty
from leaderboard_manager import append_match_results

class MatchApp:
    def __init__(self, total_players=2, cpu_opponents=1, cpu_difficulty="medium", player_names=None):
        pg.init()
        pg.display.set_caption("Tetris – Versus")

        self.total_players = max(2, min(3, int(total_players)))
        self.cpu_opponents = max(0, min(2, int(cpu_opponents)))
        if self.total_players == 2 and self.cpu_opponents > 1:
            self.cpu_opponents = 1

        self.cpu_difficulty = str(cpu_difficulty).lower().strip()
        if self.cpu_difficulty not in ("easy", "medium"):
            self.cpu_difficulty = "medium"

        self.human_players = self.total_players - self.cpu_opponents
        if self.human_players < 1:
            self.human_players = 1
            self.cpu_opponents = self.total_players - self.human_players

        if player_names is None:
            player_names = []
        self.player_names = list(player_names)
        default_names = ["Player 1", "Player 2", "Player 3"]

        while len(self.player_names) < self.total_players:
            index = len(self.player_names)
            if index < self.human_players:
                self.player_names.append(default_names[index])
            else:
                self.player_names.append(f"CPU {index - self.human_players + 1}")
        self.player_names = self.player_names[: self.total_players]

        board_width = FIELD_W * TILE_SIZE
        board_height = FIELD_H * TILE_SIZE

        max_width = 1920
        margin_top = 80
        margin_bottom = 150

        gap = 120 if self.total_players == 2 else 60

        total_boards_width = self.total_players * board_width + (self.total_players - 1) * gap
        margin_left = max(20, (max_width - total_boards_width) // 2)
        window_width = min(max_width, margin_left * 2 + total_boards_width)
        window_height = min(1200, margin_top + board_height + margin_bottom)

        while window_width > max_width and gap > 20 and self.total_players == 3:
            gap -= 5
            total_boards_width = self.total_players * board_width + (self.total_players - 1) * gap
            margin_left = max(20, (max_width - total_boards_width) // 2)
            window_width = min(max_width, margin_left * 2 + total_boards_width)

        self.screen = pg.display.set_mode((int(window_width), int(window_height)))
        self.clock = pg.time.Clock()

        self.margin_left = int(margin_left)
        self.margin_top = int(margin_top)
        self.gap = int(gap)
        self.board_width = board_width
        self.board_height = board_height

        self.images = self.load_sprites()

        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMATION_TIME_INTERVAL)

        self.games = []
        self.is_cpu_board = []
        self.cpu_agents = []
        self.board_positions = []

        for board_index in range(self.total_players):
            board_x = self.margin_left + board_index * (board_width + self.gap)
            board_y = self.margin_top
            offset_x_tiles = board_x / TILE_SIZE
            offset_y_tiles = board_y / TILE_SIZE

            self.board_positions.append((board_x, board_y))

            game = Tetris(self, offset_tiles=vec(offset_x_tiles, offset_y_tiles), is_simulation=False, solo_mode=False)
            self.games.append(game)

            is_cpu = board_index >= self.human_players
            self.is_cpu_board.append(is_cpu)
            self.cpu_agents.append(get_ai_by_difficulty(self.cpu_difficulty) if is_cpu else None)

        self.cpu_move_delay = 20
        self.cpu_move_timers = [0] * self.total_players

        self.human_controls = [
            {"left": pg.K_a, "right": pg.K_d, "rotate": pg.K_w, "down": pg.K_s},
            {"left": pg.K_j, "right": pg.K_l, "rotate": pg.K_i, "down": pg.K_k},
            {"left": pg.K_LEFT, "right": pg.K_RIGHT, "rotate": pg.K_UP, "down": pg.K_DOWN},
        ]

        self.match_finished = False
        self.results_saved = False

        self.paused = False
        self.pause_font = pg.font.Font(None, 96)

    def load_sprites(self):
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
        colours = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (255, 128, 0),
        ]
        sprites = []
        for colour in colours:
            surface = pg.Surface((TILE_SIZE, TILE_SIZE))
            surface.fill(colour)
            pg.draw.rect(surface, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surface)
        return sprites

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            for game in self.games:
                game.speed_up = False

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

    def update_cpu(self):
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

    def save_results(self):
        if not self.match_finished or self.results_saved:
            return

        is_cpu_match = self.cpu_opponents > 0
        if is_cpu_match:
            history_file = LEADERBOARD_CPU_CSV
        else:
            history_file = LEADERBOARD_2P_CSV if self.total_players == 2 else LEADERBOARD_3P_CSV

        results = []
        for board_index in range(self.total_players):
            results.append(
                {
                    "name": self.player_names[board_index],
                    "score": self.games[board_index].score,
                    "is_cpu": self.is_cpu_board[board_index],
                }
            )

        append_match_results(history_file, results)
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

            if event.type == pg.KEYDOWN and event.key == PAUSE_KEY_MATCH:
                self.toggle_pause()

            if self.paused:
                continue

            if event.type == pg.KEYDOWN:
                for human_index in range(self.human_players):
                    game = self.games[human_index]
                    if game.game_over_flag:
                        continue
                    mapping = self.human_controls[human_index]
                    if event.key == mapping["left"]:
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
        if self.paused:
            self.clock.tick(FPS)
            return

        self.update_cpu()
        for game in self.games:
            game.update()

        self.match_finished = all(game.game_over_flag for game in self.games)
        self.save_results()
        self.clock.tick(FPS)

    def draw_pause_overlay(self):
        screen_width, screen_height = self.screen.get_size()
        overlay = pg.Surface((screen_width, screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        paused_text = self.pause_font.render("PAUSED", True, (255, 255, 255))
        paused_rect = paused_text.get_rect(center=(screen_width // 2, screen_height // 2))
        self.screen.blit(paused_text, paused_rect)

        hint_text = pg.font.Font(None, 36).render("Press P to resume", True, (220, 220, 220))
        hint_rect = hint_text.get_rect(center=(screen_width // 2, screen_height // 2 + 70))
        self.screen.blit(hint_text, hint_rect)

    def draw(self):
        window_width, window_height = self.screen.get_size()
        for y in range(window_height):
            blend = y / window_height
            red = int(25 * (1 - blend) + 40 * blend)
            green = int(30 * (1 - blend) + 20 * blend)
            blue = int(50 * (1 - blend) + 60 * blend)
            pg.draw.line(self.screen, (red, green, blue), (0, y), (window_width, y))

        for game in self.games:
            game.draw()

        self.draw_labels()

        if self.paused:
            self.draw_pause_overlay()

        pg.display.flip()

    def draw_labels(self):
        heading_font = pg.font.Font(None, 42)
        score_font = pg.font.Font(None, 36)
        status_font = pg.font.Font(None, 28)

        for board_index in range(self.total_players):
            name = self.player_names[board_index]
            game = self.games[board_index]
            board_x, board_y = self.board_positions[board_index]

            name_text = heading_font.render(name, True, (255, 255, 150))
            name_rect = name_text.get_rect(centerx=board_x + self.board_width // 2, bottom=board_y - 10)
            self.screen.blit(name_text, name_rect)

            board_bottom = board_y + self.board_height
            score_text = score_font.render(f"Score: {game.score}", True, (150, 255, 150))
            score_rect = score_text.get_rect(centerx=board_x + self.board_width // 2, top=board_bottom + 10)
            self.screen.blit(score_text, score_rect)

            if game.game_over_flag:
                status_text = status_font.render("GAME OVER", True, (255, 100, 100))
                status_rect = status_text.get_rect(centerx=board_x + self.board_width // 2, top=board_bottom + 50)
                self.screen.blit(status_text, status_rect)

        if self.match_finished:
            screen_width, screen_height = self.screen.get_size()
            big_font = pg.font.Font(None, 64)
            finish_text = big_font.render("MATCH COMPLETE!", True, (255, 255, 100))
            finish_rect = finish_text.get_rect(center=(screen_width // 2, screen_height - 60))
            self.screen.blit(finish_text, finish_rect)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()
