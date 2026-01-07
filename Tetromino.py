from settings import *
import random
import pygame as pg


class Block(pg.sprite.Sprite):
    def __init__(self, tetromino, pos, is_next_piece=False):
        # Always initialize as Sprite
        pg.sprite.Sprite.__init__(self)
        
        self.tetromino = tetromino
        self.alive = True
        self.is_next_piece = is_next_piece
        
        # Set position
        if is_next_piece:
            self.pos = vec(pos) + NEXT_TETROMINO_POS
        else:
            self.pos = vec(pos) + INIT_POS_OFFSET
        
        # Get or create image
        if tetromino.image:
            self.image = tetromino.image
        else:
            # Create colored block
            self.image = pg.Surface((TILE_SIZE, TILE_SIZE))
            colors = {
                'T': (255, 0, 255),    # Purple
                'O': (255, 255, 0),    # Yellow
                'J': (0, 0, 255),      # Blue
                'L': (255, 165, 0),    # Orange
                'I': (0, 255, 255),    # Cyan
                'S': (0, 255, 0),      # Green
                'Z': (255, 0, 0)       # Red
            }
            color = colors.get(tetromino.shape, (200, 200, 200))
            self.image.fill(color)
            pg.draw.rect(self.image, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
        
        self.rect = self.image.get_rect()
        
        # Only add to sprite group if not a simulation
        if not tetromino.tetris.is_simulation and tetromino.tetris.sprite_group is not None:
            tetromino.tetris.sprite_group.add(self)

    def rotate(self, pivot_pos):
        translated = self.pos - pivot_pos
        rotated = translated.rotate(90)
        return rotated + pivot_pos

    def update(self):
        if not self.alive:
            self.kill()
            return
            
        # Update sprite position
        display_pos = self.pos
        
        if hasattr(self.tetromino.tetris, 'offset_tiles'):
            offset = self.tetromino.tetris.offset_tiles
            self.rect.topleft = (display_pos + offset) * TILE_SIZE
        else:
            self.rect.topleft = display_pos * TILE_SIZE

    def has_collided(self, test_pos):
        x, y = int(test_pos.x), int(test_pos.y)
        
        if x < 0 or x >= FIELD_W or y >= FIELD_H:
            return True
            
        if y < 0:
            return False
            
        if self.tetromino.tetris.field_array[y][x]:
            return True
            
        return False


class Tetromino:
    def __init__(self, tetris, current_shape=True):
        self.tetris = tetris
        self.shape = random.choice(list(TETROMINOES.keys()))
        self.landing = False
        self.current_shape = current_shape
        
        # Get image
        if hasattr(tetris, 'images') and tetris.images:
            self.image = random.choice(tetris.images)
        else:
            self.image = None
        
        # Create blocks
        self.blocks = []
        for pos in TETROMINOES[self.shape]:
            block = Block(self, pos, is_next_piece=not current_shape)
            self.blocks.append(block)

    @property
    def pos(self):
        if self.blocks:
            return self.blocks[0].pos
        return vec(0, 0)

    def rotate(self):
        if not self.blocks:
            return
            
        pivot_pos = self.blocks[0].pos
        new_positions = [block.rotate(pivot_pos) for block in self.blocks]
        
        if not self.has_collided(new_positions):
            for i, block in enumerate(self.blocks):
                block.pos = new_positions[i]

    def has_collided(self, positions):
        for block, pos in zip(self.blocks, positions):
            if block.has_collided(pos):
                return True
        return False

    def move(self, direction):
        if not self.blocks:
            return
            
        move_dir = MOVE_DIRECTIONS[direction]
        new_positions = [block.pos + move_dir for block in self.blocks]
        
        if not self.has_collided(new_positions):
            for block in self.blocks:
                block.pos += move_dir
        elif direction == 'down':
            self.landing = True

    def update(self):
        self.move('down')