from settings import *

import random
import pygame as pg


class Block(pg.sprite.Sprite):
    def __init__(self, tetromino, pos, is_next_piece=False):
        pg.sprite.Sprite.__init__(self)

        self.tetromino = tetromino
        self.alive = True
        self.is_next_piece = is_next_piece

        if is_next_piece:
            self.pos = vec(pos) + NEXT_TETROMINO_POS
        else:
            self.pos = vec(pos) + INIT_POS_OFFSET

        if tetromino.image:
            self.image = tetromino.image
        else:
            self.image = pg.Surface((TILE_SIZE, TILE_SIZE))
            colours_by_shape = {
                "T": (255, 0, 255),
                "O": (255, 255, 0),
                "J": (0, 0, 255),
                "L": (255, 165, 0),
                "I": (0, 255, 255),
                "S": (0, 255, 0),
                "Z": (255, 0, 0),
            }

            colour = colours_by_shape.get(tetromino.shape, (200, 200, 200))
            self.image.fill(colour)
            pg.draw.rect(self.image, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)

        self.rect = self.image.get_rect()

        if not tetromino.tetris.is_simulation and tetromino.tetris.sprite_group is not None:
            tetromino.tetris.sprite_group.add(self)

    def rotate(self, pivot_pos):
        translated_position = self.pos - pivot_pos
        rotated_position = translated_position.rotate(90)
        return rotated_position + pivot_pos

    def update(self):
        if not self.alive:
            self.kill()
            return

        block_grid_position = self.pos
        if hasattr(self.tetromino.tetris, "offset_tiles"):
            grid_offset_tiles = self.tetromino.tetris.offset_tiles
            self.rect.topleft = (block_grid_position + grid_offset_tiles) * TILE_SIZE
        else:
            self.rect.topleft = block_grid_position * TILE_SIZE

    def has_collided(self, test_pos):
        grid_x, grid_y = int(test_pos.x), int(test_pos.y)

        if grid_x < 0 or grid_x >= FIELD_W or grid_y >= FIELD_H:
            return True
        if grid_y < 0:
            return False
        if self.tetromino.tetris.field_array[grid_y][grid_x]:
            return True
        return False


class Tetromino:
    def __init__(self, tetris, current_shape=True, rng=None):
        self.tetris = tetris
        self.landing = False
        self.current_shape = current_shape

        self.random_generator = rng if rng is not None else random

        self.shape = self.random_generator.choice(list(TETROMINOES.keys()))

        if hasattr(tetris, "images") and tetris.images:
            self.image = self.random_generator.choice(tetris.images)
        else:
            self.image = None

        self.blocks = []
        for relative_pos in TETROMINOES[self.shape]:
            self.blocks.append(Block(self, relative_pos, is_next_piece=not current_shape))

    @property
    def pos(self):
        if self.blocks:
            return self.blocks[0].pos
        return vec(0, 0)

    def rotate(self):
        if not self.blocks:
            return

        pivot_pos = self.blocks[0].pos
        rotated_positions = [block.rotate(pivot_pos) for block in self.blocks]

        if not self.has_collided(rotated_positions):
            for index, block in enumerate(self.blocks):
                block.pos = rotated_positions[index]

    def has_collided(self, positions):
        for block, test_pos in zip(self.blocks, positions):
            if block.has_collided(test_pos):
                return True
        return False

    def move(self, direction):
        if not self.blocks:
            return

        move_direction_vector = MOVE_DIRECTIONS[direction]
        moved_positions = [block.pos + move_direction_vector for block in self.blocks]

        if not self.has_collided(moved_positions):
            for block in self.blocks:
                block.pos += move_direction_vector
        elif direction == "down":
            self.landing = True

    def update(self):
        self.move("down")
