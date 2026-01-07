from settings import *
import math
from Tetromino import Tetromino, Block
import pygame.freetype as ft
import pygame as pg


class Text:
    def __init__(self, app):
        self.app = app
        self.font = ft.Font(FONT_PATH)

    def draw(self):
        self.font.render_to(self.app.screen, (WIN_W * 0.595, WIN_W * 0.02),
                            text='TETRIS', fgcolor='white', size=TILE_SIZE * 1.65)
        self.font.render_to(self.app.screen, (WIN_W * 0.65, WIN_H * 0.22),
                            text='NEXT', fgcolor='white', size=TILE_SIZE * 1.4)
        self.font.render_to(self.app.screen, (WIN_W * 0.64, WIN_H * 0.67),
                            text='SCORE', fgcolor='white', size=TILE_SIZE * 1.4)
        self.font.render_to(self.app.screen, (WIN_W * 0.64, WIN_H * 0.8),
                            text=f'{self.app.tetris.score}', fgcolor='white', size=TILE_SIZE * 1.8)


class Tetris:
    def __init__(self, app, offset_tiles=None, is_simulation=False):
        self.app = app
        self.is_simulation = is_simulation
        
        # Sprite group for real games
        if not is_simulation:
            self.sprite_group = pg.sprite.Group()
        else:
            self.sprite_group = None
        
        self.offset_tiles = offset_tiles if offset_tiles is not None else vec(0, 0)
        
        # Store images
        if hasattr(app, 'images'):
            self.images = app.images
        else:
            self.images = []
        
        # Initialize game field
        self.field_array = [[0 for x in range(FIELD_W)] for y in range(FIELD_H)]
        
        # Game state
        self.speed_up = False
        self.score = 0
        self.full_lines = 0
        self.lines_cleared = 0
        self.game_over_flag = False
        self.points_per_line = {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}
        
        # Create tetrominoes
        self.tetromino = Tetromino(self, current_shape=True)
        self.next_tetromino = Tetromino(self, current_shape=False)

    def get_score(self):
        self.score += self.points_per_line[self.full_lines]
        self.lines_cleared += self.full_lines
        self.full_lines = 0

    def check_full_line(self):
        row = FIELD_H - 1
        for y in range(FIELD_H - 1, -1, -1):
            line_full = True
            for x in range(FIELD_W):
                if not self.field_array[y][x]:
                    line_full = False
                    break
            
            if not line_full:
                if row != y:
                    for x in range(FIELD_W):
                        self.field_array[row][x] = self.field_array[y][x]
                        if isinstance(self.field_array[row][x], Block):
                            self.field_array[row][x].pos = vec(x, row)
                row -= 1
            else:
                self.full_lines += 1
                for x in range(FIELD_W):
                    if isinstance(self.field_array[y][x], Block):
                        self.field_array[y][x].alive = False
                        self.field_array[y][x].kill()
                    self.field_array[y][x] = 0

    def put_tetromino_blocks_in_array(self):
        for block in self.tetromino.blocks:
            x, y = int(block.pos.x), int(block.pos.y)
            if 0 <= x < FIELD_W and 0 <= y < FIELD_H:
                self.field_array[y][x] = block

    def check_game_over(self):
        # Check if spawn area is blocked
        for block in self.tetromino.blocks:
            x, y = int(block.pos.x), int(block.pos.y)
            if y <= 1 and self.field_array[y][x]:
                return True
        return False

    def check_tetromino_landing(self):
        if self.tetromino.landing:
            # Lock piece
            self.put_tetromino_blocks_in_array()
            
            # Check game over
            if self.check_game_over():
                self.game_over_flag = True
                return
            
            # Clear lines and update score
            self.check_full_line()
            self.get_score()
            
            # Reset speed
            self.speed_up = False
            
            # Spawn new piece
            self.tetromino = self.next_tetromino
            self.tetromino.current_shape = True
            
            # Convert from preview to play position
            for block in self.tetromino.blocks:
                block.pos = vec(block.pos.x - NEXT_TETROMINO_POS.x + INIT_POS_OFFSET.x,
                              block.pos.y - NEXT_TETROMINO_POS.y + INIT_POS_OFFSET.y)
                block.is_next_piece = False
            
            # Create new next piece
            self.next_tetromino = Tetromino(self, current_shape=False)
            self.tetromino.landing = False

    def control(self, pressed_key):
        if pressed_key == pg.K_LEFT:
            self.tetromino.move(direction='left')
        elif pressed_key == pg.K_RIGHT:
            self.tetromino.move(direction='right')
        elif pressed_key == pg.K_UP:
            self.tetromino.rotate()
        elif pressed_key == pg.K_DOWN:
            self.speed_up = True

    def draw_grid(self):
        if self.is_simulation:
            return
            
        for x in range(FIELD_W):
            for y in range(FIELD_H):
                pg.draw.rect(
                    self.app.screen, (50, 70, 110),
                    ((x + self.offset_tiles.x) * TILE_SIZE,
                     (y + self.offset_tiles.y) * TILE_SIZE,
                     TILE_SIZE, TILE_SIZE), 1)

    def update(self):
        if self.game_over_flag:
            return
            
        if self.speed_up:
            trigger = self.app.fast_animation_trigger
        else:
            trigger = self.app.animation_trigger
        
        if trigger:
            self.tetromino.update()
            self.check_tetromino_landing()
        
        # Update sprite positions
        if not self.is_simulation and self.sprite_group:
            self.sprite_group.update()

    def draw(self):
        if self.is_simulation:
            return
            
        self.draw_grid()
        if self.sprite_group:
            self.sprite_group.draw(self.app.screen)

    def get_board_matrix(self):
        matrix = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]
        
        # Add landed blocks
        for y in range(FIELD_H):
            for x in range(FIELD_W):
                if self.field_array[y][x]:
                    matrix[y][x] = 1
        
        # Add current falling piece
        for block in self.tetromino.blocks:
            x, y = int(block.pos.x), int(block.pos.y)
            if 0 <= x < FIELD_W and 0 <= y < FIELD_H:
                matrix[y][x] = 1
                
        return matrix

    def clone(self):
        """Create a simulation clone"""
        class DummyApp:
            def __init__(self, images):
                self.images = images
                self.animation_trigger = True
                self.fast_animation_trigger = False
        
        # Create simulation
        clone = Tetris(DummyApp(self.images), 
                      offset_tiles=self.offset_tiles, 
                      is_simulation=True)
        
        # Copy field array
        for y in range(FIELD_H):
            for x in range(FIELD_W):
                clone.field_array[y][x] = 1 if self.field_array[y][x] else 0
        
        # Copy game state
        clone.score = self.score
        clone.lines_cleared = self.lines_cleared
        clone.game_over_flag = self.game_over_flag
        
        # Simple tetromino clone for simulation
        clone.tetromino = self._simple_clone_tetromino(self.tetromino, clone, is_current=True)
        clone.next_tetromino = self._simple_clone_tetromino(self.next_tetromino, clone, is_current=False)
        
        return clone
    
    def _simple_clone_tetromino(self, original, target_tetris, is_current):
        """Simple clone for simulation - no sprites"""
        class SimpleBlock:
            def __init__(self, pos, is_next_piece):
                if is_next_piece:
                    self.pos = vec(pos) + NEXT_TETROMINO_POS
                else:
                    self.pos = vec(pos) + INIT_POS_OFFSET
                self.is_next_piece = is_next_piece
            
            def rotate(self, pivot_pos):
                translated = self.pos - pivot_pos
                rotated = translated.rotate(90)
                return rotated + pivot_pos
            
            def has_collided(self, test_pos):
                x, y = int(test_pos.x), int(test_pos.y)
                if x < 0 or x >= FIELD_W or y >= FIELD_H:
                    return True
                if y < 0:
                    return False
                if target_tetris.field_array[y][x]:
                    return True
                return False
        
        class SimpleTetromino:
            def __init__(self, shape, blocks_data, is_current):
                self.shape = shape
                self.landing = False
                self.current_shape = is_current
                self.blocks = []
                for pos, is_next in blocks_data:
                    self.blocks.append(SimpleBlock(pos, is_next))
            
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
        
        # Get block data from original
        blocks_data = []
        for block in original.blocks:
            # Calculate original position
            if block.is_next_piece:
                original_pos = block.pos - NEXT_TETROMINO_POS
            else:
                original_pos = block.pos - INIT_POS_OFFSET
            blocks_data.append((original_pos, block.is_next_piece))
        
        return SimpleTetromino(original.shape, blocks_data, is_current)

    def get_possible_moves(self):
        """Get all possible moves using simple simulation"""
        moves = []
        
        # Create a simple simulation
        sim = self.clone()
        
        # Test all rotations
        for rot in range(4):
            rot_sim = sim.clone()
            
            # Apply rotation
            for _ in range(rot):
                rot_sim.tetromino.rotate()
            
            # Test all horizontal positions
            for x in range(FIELD_W):
                test = rot_sim.clone()
                
                # Move to target x
                current_x = int(test.tetromino.blocks[0].pos.x)
                shift = x - current_x
                
                # Try to move horizontally
                can_move = True
                for _ in range(abs(shift)):
                    direction = vec(1 if shift > 0 else -1, 0)
                    new_positions = [b.pos + direction for b in test.tetromino.blocks]
                    if test.tetromino.has_collided(new_positions):
                        can_move = False
                        break
                    for b in test.tetromino.blocks:
                        b.pos += direction
                
                if not can_move:
                    continue
                
                # Hard drop
                dropped = False
                while not dropped:
                    new_positions = [b.pos + vec(0, 1) for b in test.tetromino.blocks]
                    if test.tetromino.has_collided(new_positions):
                        dropped = True
                    else:
                        for b in test.tetromino.blocks:
                            b.pos.y += 1
                
                # Check if valid
                valid = True
                for block in test.tetromino.blocks:
                    x_pos, y_pos = int(block.pos.x), int(block.pos.y)
                    if x_pos < 0 or x_pos >= FIELD_W or y_pos < 0 or y_pos >= FIELD_H:
                        valid = False
                        break
                
                if valid:
                    moves.append((rot, x))
        
        return moves

    def apply_ai_move(self, move):
        """Apply an AI-chosen move"""
        if not move or self.game_over_flag:
            return
            
        rot, target_x = move
        
        # Apply rotation
        for _ in range(rot):
            self.tetromino.rotate()
        
        # Move horizontally
        current_x = int(self.tetromino.blocks[0].pos.x)
        shift = target_x - current_x
        
        if shift != 0:
            direction = vec(1 if shift > 0 else -1, 0)
            for _ in range(abs(shift)):
                new_positions = [b.pos + direction for b in self.tetromino.blocks]
                if self.tetromino.has_collided(new_positions):
                    break
                for b in self.tetromino.blocks:
                    b.pos += direction
        
        # Hard drop
        while True:
            new_positions = [b.pos + vec(0, 1) for b in self.tetromino.blocks]
            if self.tetromino.has_collided(new_positions):
                self.tetromino.landing = True
                break
            for b in self.tetromino.blocks:
                b.pos.y += 1
        
        # Process landing
        if self.tetromino.landing:
            self.check_tetromino_landing()