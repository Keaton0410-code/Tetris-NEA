from settings import *
from Tetromino import Tetromino, Block

import random
import pygame.freetype as ft
import pygame as pg

class Text:
    def __init__(self, app):
        self.app = app
        try:
            self.font = ft.Font(FONT_PATH)
            self.using_freetype = True
        except (FileNotFoundError, OSError):
            # Fall back to regular pygame font if the .ttf is missing
            self.font = None
            self.using_freetype = False

    def draw(self):
        if self.using_freetype and self.font:
            # FreeType path — renders directly onto the surface
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.595, WIN_W * 0.02), text='TETRIS',
                fgcolor='white',size=TILE_SIZE * 1.65) 
            
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.65, WIN_H * 0.22), text='NEXT',
                fgcolor='white', size=TILE_SIZE * 1.4)
            
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.64, WIN_H * 0.67), text='SCORE', 
                fgcolor='white', size=TILE_SIZE * 1.4)
            
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.64, WIN_H * 0.8), text=f'{self.app.tetris.score}',
                fgcolor='white', size=TILE_SIZE * 1.8)
        else:
            fallback_font_large = pg.font.Font(None, int(TILE_SIZE * 1.65))
            fallback_font_medium = pg.font.Font(None, int(TILE_SIZE * 1.4))
            fallback_font_score  = pg.font.Font(None, int(TILE_SIZE * 1.8))

            tetris_text  = fallback_font_large.render('TETRIS', True, 'white')
            next_text    = fallback_font_medium.render('NEXT',True, 'white')
            score_label  = fallback_font_medium.render('SCORE', True, 'white')
            score_value  = fallback_font_score.render(f'{self.app.tetris.score}',True, 'white')

            self.app.screen.blit(tetris_text,(WIN_W * 0.595,WIN_W * 0.02))
            self.app.screen.blit(next_text,(WIN_W * 0.65,WIN_H * 0.22))
            self.app.screen.blit(score_label,(WIN_W * 0.64, WIN_H * 0.67))
            self.app.screen.blit(score_value,(WIN_W * 0.64,WIN_H * 0.8))

class Tetris:
    def __init__(self, app, offset_tiles=None, is_simulation=False, random_seed=None):
        self.app = app
        self.is_simulation = is_simulation

        # Each board gets its own RNG
        self.random_generator = random.Random(random_seed)

        # Only non-simulation games need a sprite group
        if not is_simulation:
            self.sprite_group = pg.sprite.Group()
        else:
            self.sprite_group = None

        self.offset_tiles = offset_tiles if offset_tiles is not None else vec(0, 0)

        # Tile images shared across all boards in a match
        if hasattr(app,'images'):
            self.images = app.images
        else:
            self.images = []

        # 2D grid 0 = empty, Block = occupied
        self.field_array = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

        # Game state
        self.speed_up = False
        self.score = 0
        self.full_lines = 0
        self.lines_cleared = 0
        self.game_over_flag = False

        self.points_per_line = {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}

        self.tetromino      = Tetromino(self, current_shape=True,  rng=self.random_generator)
        self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)

    #Scoring  line clearing
    def get_score(self):
        """Adds points for any lines that were just cleared and resets the counter."""
        self.score += self.points_per_line[self.full_lines]
        self.lines_cleared += self.full_lines
        self.full_lines = 0

    def check_full_line(self):
        """Scans for complete rows, removes them, and shifts everything above down."""
        target_row_index = FIELD_H - 1

        for current_row_index in range(FIELD_H - 1, -1, -1):
            row_is_full = True
            for column_index in range(FIELD_W):
                if not self.field_array[current_row_index][column_index]:
                    row_is_full = False
                    break

            if not row_is_full:
                #Copy this row down to the target position if it has moved
                if target_row_index != current_row_index:
                    for column_index in range(FIELD_W):
                        self.field_array[target_row_index][column_index] = self.field_array[current_row_index][column_index]
                        if isinstance(self.field_array[target_row_index][column_index], Block):
                            self.field_array[target_row_index][column_index].pos = vec(column_index, target_row_index)
                target_row_index -= 1
            else:
                self.full_lines += 1
                for column_index in range(FIELD_W):
                    if isinstance(self.field_array[current_row_index][column_index], Block):
                        self.field_array[current_row_index][column_index].alive = False
                        self.field_array[current_row_index][column_index].kill()
                    self.field_array[current_row_index][column_index] = 0

    # Piece locking & landing

    def lock_piece(self):
        """Writes the current tetromino's blocks into the field grid."""
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if 0 <= grid_x < FIELD_W and 0 <= grid_y < FIELD_H:
                self.field_array[grid_y][grid_x] = block

    def check_game_over(self):
        """Returns True if any block of the current piece is stuck in the top two rows."""
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if grid_y <= 1 and self.field_array[grid_y][grid_x]:
                return True
        return False

    def check_landing(self):
        if self.tetromino.landing:
            #Freeze the piece into the grid
            self.lock_piece()

            # Game over if the piece landed at the very top
            if self.check_game_over():
                self.game_over_flag = True
                return

            # Clear any completed rows and award points
            self.check_full_line()
            self.get_score()

            # Cancel any active fast-drop
            self.speed_up = False

            # Promote the preview piece to the active piece
            self.tetromino = self.next_tetromino
            self.tetromino.current_shape = True

            # Move its blocks from the preview position to the spawn position
            for block in self.tetromino.blocks:
                block.pos = vec(
                    block.pos.x - NEXT_TETROMINO_POS.x + INIT_POS_OFFSET.x,
                    block.pos.y - NEXT_TETROMINO_POS.y + INIT_POS_OFFSET.y)
                block.is_next_piece = False

            self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)
            self.tetromino.landing = False

    # Controls
    def control(self, pressed_key):
        """solo controls (arrow keys)."""
        if pressed_key == pg.K_LEFT:
            self.tetromino.move(direction='left')
        elif pressed_key == pg.K_RIGHT:
            self.tetromino.move(direction='right')
        elif pressed_key == pg.K_UP:
            self.tetromino.rotate()
        elif pressed_key == pg.K_DOWN:
            self.speed_up = True

    def handle_action(self, action_name):
        if action_name == "left":
            self.tetromino.move(direction='left')
        elif action_name == "right":
            self.tetromino.move(direction='right')
        elif action_name == "rotate":
            self.tetromino.rotate()
        elif action_name == "down":
            self.speed_up = True

    # Rendering
    def draw_grid(self):
        """Draws the faint grid lines behind the playing field."""
        if self.is_simulation:
            return

        for grid_x in range(FIELD_W):
            for grid_y in range(FIELD_H):
                pg.draw.rect(
                    self.app.screen,
                    (50, 70, 110),
                    ((grid_x + self.offset_tiles.x) * TILE_SIZE, (grid_y + self.offset_tiles.y) * TILE_SIZE, TILE_SIZE, TILE_SIZE),1)

    def update(self):
        if self.game_over_flag:
            return

        animation_trigger = self.app.fast_animation_trigger if self.speed_up else self.app.animation_trigger

        if animation_trigger:
            self.tetromino.update()
            self.check_landing()

        if not self.is_simulation and self.sprite_group:
            self.sprite_group.update()

    def draw(self):
        if self.is_simulation:
            return

        self.draw_grid()
        if self.sprite_group:
            self.sprite_group.draw(self.app.screen)

    # AI helpers
    def get_board(self):
        board_matrix = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

        # Mark every occupied cell from landed blocks
        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                if self.field_array[grid_y][grid_x]:
                    board_matrix[grid_y][grid_x] = 1

        # Overlay the active falling piece
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if 0 <= grid_x < FIELD_W and 0 <= grid_y < FIELD_H:
                board_matrix[grid_y][grid_x] = 1
        return board_matrix

    def clone(self):
        class DummyApp:
            def __init__(self, images):
                self.images = images
                self.animation_trigger = True
                self.fast_animation_trigger = False

        sim = Tetris(DummyApp(self.images), offset_tiles=self.offset_tiles,is_simulation=True, random_seed=None)

        # Copy the grid cell by cell (1 = occupied, 0 = empty)
        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                sim.field_array[grid_y][grid_x] = 1 if self.field_array[grid_y][grid_x] else 0

        # Mirror game state
        sim.score = self.score
        sim.lines_cleared = self.lines_cleared
        sim.game_over_flag  = self.game_over_flag

        sim.tetromino = self.clone_tetromino(self.tetromino, sim, is_current=True)
        sim.next_tetromino = self.clone_tetromino(self.next_tetromino, sim, is_current=False)
        return sim

    def clone_tetromino(self, original_tetromino, target_tetris, is_current):
        class SimpleBlock:
            """A block with no sprite just position and collision logic."""
            def __init__(self, pos, is_next_piece):
                # Place at the correct offset depending on whether it's a preview piece
                if is_next_piece:
                    self.pos = vec(pos) + NEXT_TETROMINO_POS
                else:
                    self.pos = vec(pos) + INIT_POS_OFFSET
                self.is_next_piece = is_next_piece

            def rotate(self, pivot_pos):
                # Rotate 90 degrees around the pivot
                translated = self.pos - pivot_pos
                rotated    = translated.rotate(90)
                return rotated + pivot_pos

            def has_collided(self, test_pos):
                grid_x, grid_y = int(test_pos.x), int(test_pos.y)
                # Out of bounds on left right or bottom
                if grid_x < 0 or grid_x >= FIELD_W or grid_y >= FIELD_H:
                    return True
                #Above the top edge is fine (pieces spawn there)
                if grid_y < 0:
                    return False
                #Occupied cell
                if target_tetris.field_array[grid_y][grid_x]:
                    return True
                return False

        class SimpleTetromino:
            def __init__(self, shape, blocks_data, is_current):
                self.shape = shape
                self.landing = False
                self.current_shape = is_current
                self.blocks = []
                for relative_pos, is_next_piece in blocks_data:
                    self.blocks.append(SimpleBlock(relative_pos, is_next_piece))

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
                # Only apply if none of the new positions collide
                if not self.has_collided(new_positions):
                    for i, block in enumerate(self.blocks):
                        block.pos = new_positions[i]

            def has_collided(self, positions):
                for block,test_pos in zip(self.blocks, positions):
                    if block.has_collided(test_pos):
                        return True
                return False

            def move(self, direction):
                if not self.blocks:
                    return
                move_vector = MOVE_DIRECTIONS[direction]
                new_positions = [block.pos + move_vector for block in self.blocks]
                if not self.has_collided(new_positions):
                    for block in self.blocks:
                        block.pos += move_vector
                elif direction == 'down':
                    self.landing = True

            def update(self):
                self.move('down')

        # Extract each block's position relative to its base offset
        blocks_data = []
        for block in original_tetromino.blocks:
            if block.is_next_piece:
                original_relative_pos = block.pos - NEXT_TETROMINO_POS
            else:
                original_relative_pos = block.pos - INIT_POS_OFFSET
            blocks_data.append((original_relative_pos, block.is_next_piece))
        return SimpleTetromino(original_tetromino.shape, blocks_data, is_current)

    def get_possible_moves(self):
        possible_moves = []
        base_sim = self.clone()

        for rotation_count in range(4):
            # Clone once per rotation so each column test starts from the same rotated state
            rotated_sim = base_sim.clone()

            # Apply the rotation
            for _ in range(rotation_count):
                rotated_sim.tetromino.rotate()

            for target_x in range(FIELD_W):
                test_sim = rotated_sim.clone()

                current_x = int(test_sim.tetromino.blocks[0].pos.x)
                horizontal_shift = target_x - current_x

                can_move_horizontally = True
                for _ in range(abs(horizontal_shift)):
                    step = vec(1 if horizontal_shift > 0 else -1, 0)
                    new_positions = [block.pos + step for block in test_sim.tetromino.blocks]
                    if test_sim.tetromino.has_collided(new_positions):
                        can_move_horizontally = False
                        break
                    for block in test_sim.tetromino.blocks:
                        block.pos += step
                if not can_move_horizontally:
                    continue

                # Hard-drop keep moving down until we collide
                while True:
                    new_positions = [block.pos + vec(0, 1) for block in test_sim.tetromino.blocks]
                    if test_sim.tetromino.has_collided(new_positions):
                        break
                    for block in test_sim.tetromino.blocks:
                        block.pos.y += 1

                # Final bounds check make sure every block is inside the grid
                is_valid_move = True
                for block in test_sim.tetromino.blocks:
                    grid_x, grid_y = int(block.pos.x), int(block.pos.y)
                    if grid_x < 0 or grid_x >= FIELD_W or grid_y < 0 or grid_y >= FIELD_H:
                        is_valid_move = False
                        break
                if is_valid_move:
                    possible_moves.append((rotation_count, target_x))

        return possible_moves

    def apply_ai_move(self, move):
        if not move or self.game_over_flag:
            return
        rotation_count, target_x = move
        # Rotate first
        for _ in range(rotation_count):
            self.tetromino.rotate()

        # Slide horizontally one tile at a time
        current_x = int(self.tetromino.blocks[0].pos.x)
        horizontal_shift = target_x - current_x

        if horizontal_shift != 0:
            step = vec(1 if horizontal_shift > 0 else -1, 0)
            for _ in range(abs(horizontal_shift)):
                new_positions = [block.pos + step for block in self.tetromino.blocks]
                if self.tetromino.has_collided(new_positions):
                    break
                for block in self.tetromino.blocks:
                    block.pos += step

        # Harddrop
        while True:
            new_positions = [block.pos + vec(0, 1) for block in self.tetromino.blocks]
            if self.tetromino.has_collided(new_positions):
                self.tetromino.landing = True
                break
            for block in self.tetromino.blocks:
                block.pos.y += 1
        if self.tetromino.landing:
            self.check_landing()