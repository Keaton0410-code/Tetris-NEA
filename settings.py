import pygame as pg

#Vector type used throughout the project 
vec = pg.math.Vector2
Vector2 = pg.math.Vector2  

#Performance / timing settings 
FPS = 60

ANIMATION_TIME_INTERVAL = 300
FAST_ANIMAMATION_TIME_INTERVAL = 50  # note: name kept for compatibility

FIELD_COLOR = (20, 30, 50)
BG_COLOUR = (10, 20, 40)

FIELD_COLOUR = FIELD_COLOR
BACKGROUND_COLOUR = BG_COLOUR

# Assets / paths directories
SPRITE_DIRECTORY_PATH = 'Tetris-NEA-main/Assets/sprites'
FONT_PATH = 'Tetris-NEA/Font-main/Game-Font 2.ttf'

# Grid / window sizing
TILE_SIZE = 50

FIELD_SIZE = FIELD_W, FIELD_H = 10, 20
FIELD_RES = FIELD_W * TILE_SIZE, FIELD_H * TILE_SIZE

FIELD_SCALE_WIDTH, FIELD_SCALE_HEIGHT = 1.7, 1.0
WIN_RES = WIN_W, WIN_H = FIELD_RES[0] * FIELD_SCALE_WIDTH, FIELD_RES[1] * FIELD_SCALE_HEIGHT

SCREEN_RES = (1920, 1080)

WINDOW_RESOLUTION = WIN_RES
WINDOW_WIDTH = WIN_W
WINDOW_HEIGHT = WIN_H

# Spawn positions
INIT_POS_OFFSET = vec(FIELD_W // 2 - 1, 0)
NEXT_TETROMINO_POS = vec(FIELD_W + 1, 3)

# Optional clearer aliases
INITIAL_SPAWN_OFFSET = INIT_POS_OFFSET
NEXT_PIECE_PREVIEW_POSITION = NEXT_TETROMINO_POS

#Movement pos updates 
MOVE_DIRECTIONS = {
    'left': vec(-1, 0),
    'right': vec(1, 0),
    'down': vec(0, 1)}

#Tetrominoes / shapes
TETROMINOES = {
    'T': [(0, 0), (-1, 0), (1, 0), (0, -1)],
    'O': [(0, 0), (0, -1), (1, 0), (1, -1)],
    'J': [(0, 0), (-1, 0), (0, -1), (0, -2)],
    'L': [(0, 0), (1, 0), (0, -1), (0, -2)],
    'I': [(0, 0), (0, 1), (0, -1), (0, -2)],
    'S': [(0, 0), (-1, 0), (0, -1), (1, -1)],
    'Z': [(0, 0), (1, 0), (0, -1), (-1, -1)]}
