import pygame as pg

vec = pg.math.Vector2
Vector2 = pg.math.Vector2

# Performance / timing settings
FPS = 60

ANIMATION_TIME_INTERVAL = 300
FAST_ANIMAMATION_TIME_INTERVAL = 50

#Colours
FIELD_COLOR = (20, 30, 50)
BG_COLOUR = (10, 20, 40)

# Optional aliases (helps readability in write-up)
FIELD_COLOUR = FIELD_COLOR
BACKGROUND_COLOUR = BG_COLOUR

# Assets / paths directories
SPRITE_DIRECTORY_PATH = 'Assets/sprites'
FONT_PATH = 'Font/font.ttf'

# Grid / window sizing
TILE_SIZE = 50
FIELD_SIZE = FIELD_W, FIELD_H = 10, 20
FIELD_RES = FIELD_W * TILE_SIZE, FIELD_H * TILE_SIZE

FIELD_SCALE_WIDTH, FIELD_SCALE_HEIGHT = 1.7, 1.0
WIN_RES = WIN_W, WIN_H = FIELD_RES[0] * FIELD_SCALE_WIDTH, FIELD_RES[1] * FIELD_SCALE_HEIGHT

#Fixed full screen style resolution
SCREEN_RES = (1920, 1080)

#Aliases 
WINDOW_RESOLUTION = WIN_RES
WINDOW_WIDTH = WIN_W
WINDOW_HEIGHT = WIN_H

#Spawn positions
INIT_POS_OFFSET = vec(FIELD_W // 2 - 1, 0)
NEXT_TETROMINO_POS = vec(FIELD_W + 1, 3)
INITIAL_SPAWN_OFFSET = INIT_POS_OFFSET
NEXT_PIECE_PREVIEW_POSITION = NEXT_TETROMINO_POS

#Move position updates
MOVE_DIRECTIONS = {
    'left': vec(-1, 0),
    'right': vec(1, 0),
    'down': vec(0, 1),}

# Tetrominoes / shapes
TETROMINOES = {
    'T': [(0, 0), (-1, 0), (1, 0), (0, -1)],
    'O': [(0, 0), (0, -1), (1, 0), (1, -1)],
    'J': [(0, 0), (-1, 0), (0, -1), (0, -2)],
    'L': [(0, 0), (1, 0), (0, -1), (0, -2)],
    'I': [(0, 0), (0, 1), (0, -1), (0, -2)],
    'S': [(0, 0), (-1, 0), (0, -1), (1, -1)],
    'Z': [(0, 0), (1, 0), (0, -1), (-1, -1)],}

# How many total boards (players) are supported in match modes
MIN_MATCH_PLAYERS = 2
MAX_MATCH_PLAYERS = 3

MATCH_TOP_MARGIN_TILES = 2
MATCH_LEFT_MARGIN_TILES = 1
MATCH_GAP_BETWEEN_BOARDS_TILES = 2

# calculated offsets for each board (in tiles).
#These offsets are used when you create each Tetris instance.
PLAYER_BOARD_OFFSETS_TILES = [
    vec(MATCH_LEFT_MARGIN_TILES + 0 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),
    vec(MATCH_LEFT_MARGIN_TILES + 1 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),
    vec(MATCH_LEFT_MARGIN_TILES + 2 * (FIELD_W + MATCH_GAP_BETWEEN_BOARDS_TILES), MATCH_TOP_MARGIN_TILES),]

PLAYER_CONTROLS = {
    1: {  # Player 1: WASD
        'left': pg.K_a,
        'right': pg.K_d,
        'rotate': pg.K_w,   # rotate
        'down': pg.K_s,},     # soft drop

    2: {  # Player 2: IJKL
        'left': pg.K_j,
        'right': pg.K_l,
        'rotate': pg.K_i, # rotate
        'down': pg.K_k,},

    3: {  # Player 3: Arrow keys
        'left': pg.K_LEFT,
        'right': pg.K_RIGHT,
        'rotate': pg.K_UP,  # rotate
        'down': pg.K_DOWN,},} # soft drop

#CSV leaderboards
LEADERBOARD_HUMAN_CSV = "Leaderboard.csv"
LEADERBOARD_CPU_CSV = "Leaderboard_CPU.csv"

#default names 
DEFAULT_PLAYER_NAMES = {
    1: "Player 1",
    2: "Player 2",
    3: "Player 3",}

DEFAULT_CPU_NAMES = {
    "easy": "CPU Easy",
    "medium": "CPU Medium",}

CPU_MOVE_DELAY_FRAMES = {
    "easy": 20,
    "medium": 10,}

MATCH_WINDOW_RES = SCREEN_RES