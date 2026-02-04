import pygame as pg

vec = pg.math.Vector2
Vector2 = pg.math.Vector2

FPS = 60

ANIMATION_TIME_INTERVAL = 300
FAST_ANIMATION_TIME_INTERVAL = 50

FIELD_COLOUR = (20, 30, 50)
BACKGROUND_COLOUR = (10, 20, 40)

SPRITE_DIRECTORY_PATH = "Assets/sprites"
FONT_PATH = "Font/font.ttf"

TILE_SIZE = 50
FIELD_SIZE = FIELD_W, FIELD_H = 10, 20
FIELD_RES = FIELD_W * TILE_SIZE, FIELD_H * TILE_SIZE

FIELD_SCALE_WIDTH, FIELD_SCALE_HEIGHT = 1.7, 1.0
WIN_RES = WIN_W, WIN_H = FIELD_RES[0] * FIELD_SCALE_WIDTH, FIELD_RES[1] * FIELD_SCALE_HEIGHT

SCREEN_RES = (1920, 1080)

WINDOW_RESOLUTION = WIN_RES
WINDOW_WIDTH = WIN_W
WINDOW_HEIGHT = WIN_H

INIT_POS_OFFSET = vec(FIELD_W // 2 - 1, 0)
NEXT_TETROMINO_POS = vec(FIELD_W + 1, 3)
INITIAL_SPAWN_OFFSET = INIT_POS_OFFSET
NEXT_PIECE_PREVIEW_POSITION = NEXT_TETROMINO_POS

MOVE_DIRECTIONS = {
    "left": vec(-1, 0),
    "right": vec(1, 0),
    "down": vec(0, 1),
}

TETROMINOES = {
    "T": [(0, 0), (-1, 0), (1, 0), (0, -1)],
    "O": [(0, 0), (0, -1), (1, 0), (1, -1)],
    "J": [(0, 0), (-1, 0), (0, -1), (0, -2)],
    "L": [(0, 0), (1, 0), (0, -1), (0, -2)],
    "I": [(0, 0), (0, 1), (0, -1), (0, -2)],
    "S": [(0, 0), (-1, 0), (0, -1), (1, -1)],
    "Z": [(0, 0), (1, 0), (0, -1), (-1, -1)],
}

MIN_MATCH_PLAYERS = 2
MAX_MATCH_PLAYERS = 3

MATCH_TOP_MARGIN_TILES = 2
MATCH_LEFT_MARGIN_TILES = 1
MATCH_GAP_BETWEEN_BOARDS_TILES = 2

PLAYER_BOARD_OFFSETS_TILES = [
    vec(MATCH_LEFT_MARGIN_TILES + 0 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),
    vec(MATCH_LEFT_MARGIN_TILES + 1 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),
    vec(MATCH_LEFT_MARGIN_TILES + 2 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),
]

PLAYER_CONTROLS = {
    1: {"left": pg.K_a, "right": pg.K_d, "rotate": pg.K_w, "down": pg.K_s},
    2: {"left": pg.K_j, "right": pg.K_l, "rotate": pg.K_i, "down": pg.K_k},
    3: {"left": pg.K_LEFT, "right": pg.K_RIGHT, "rotate": pg.K_UP, "down": pg.K_DOWN},
}

SPEED_INTERVALS_MS = {
    1: 420,
    2: 340,
    3: 280,
    4: 220,
    5: 160,
}

SPEED_SCORE_MULTIPLIERS = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.5,
    5: 3.0,
}

LEVEL_START = 1
LINES_PER_LEVEL = 10


def level_base_interval_ms(level: int) -> int:
    level = max(1, int(level))
    return max(60, ANIMATION_TIME_INTERVAL - (level - 1) * 20)


def combined_fall_interval_ms(manual_speed: int, level: int) -> int:
    manual_speed = max(1, min(5, int(manual_speed)))
    manual_interval = SPEED_INTERVALS_MS[manual_speed]
    level_interval = level_base_interval_ms(level)
    ratio = level_interval / ANIMATION_TIME_INTERVAL
    return max(50, int(manual_interval * ratio))


PAUSE_KEY_SOLO = pg.K_p
PAUSE_KEY_MATCH = pg.K_p

LINE_CLEAR_PHRASES = {
    1: "SINGLE!",
    2: "DOUBLE!!",
    3: "TRIPLE!!!",
    4: "TETRIS!!!!",
}

LEADERBOARD_SOLO_CSV = "Leaderboard_Solo.csv"
LEADERBOARD_2P_CSV = "Leaderboard_2P.csv"
LEADERBOARD_3P_CSV = "Leaderboard_3P.csv"
LEADERBOARD_CPU_CSV = "Leaderboard_CPU.csv"

DEFAULT_PLAYER_NAMES = {1: "Player 1", 2: "Player 2", 3: "Player 3"}
DEFAULT_CPU_NAMES = {"easy": "CPU Easy", "medium": "CPU Medium"}

CPU_MOVE_DELAY_FRAMES = {"easy": 20, "medium": 10}

MATCH_WINDOW_RES = SCREEN_RES
