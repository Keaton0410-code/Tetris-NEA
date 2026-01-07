import pygame as pg

vec = pg.math.Vector2

FPS = 60
FIELD_COLOR = (20, 30, 50)
BG_COLOUR = (10, 20, 40)

SPRITE_DIRECTORY_PATH = 'Tetris NEA/Assets/sprites'
FONT_PATH = 'Tetris NEA/Font/Game-Font 2.ttf'

ANIMATION_TIME_INTERVAL = 300
FAST_ANIMAMATION_TIME_INTERVAL = 50

TILE_SIZE = 50
FIELD_SIZE = FIELD_W, FIELD_H = 10, 20
FIELD_RES = FIELD_W * TILE_SIZE, FIELD_H * TILE_SIZE

FIELD_SCALE_WIDTH, FIELD_SCALE_HEIGHT = 1.7, 1.0
WIN_RES = WIN_W, WIN_H = FIELD_RES[0] * FIELD_SCALE_WIDTH, FIELD_RES[1] * FIELD_SCALE_HEIGHT

SCREEN_RES = (1920, 1080)

INIT_POS_OFFSET = vec(FIELD_W // 2 - 1, 0)
NEXT_TETROMINO_POS = vec(FIELD_W + 1, 3)

MOVE_DIRECTIONS = {'left': vec(-1, 0), 
                   'right': vec(1, 0), 
                   'down': vec(0, 1)}

TETROMINOES = {
    'T': [(0, 0), (-1, 0), (1, 0), (0, -1)],
    'O': [(0, 0), (0, -1), (1, 0), (1, -1)],
    'J': [(0, 0), (-1, 0), (0, -1), (0, -2)],
    'L': [(0, 0), (1, 0), (0, -1), (0, -2)],
    'I': [(0, 0), (0, 1), (0, -1), (0, -2)],
    'S': [(0, 0), (-1, 0), (0, -1), (1, -1)],
    'Z': [(0, 0), (1, 0), (0, -1), (-1, -1)]
}