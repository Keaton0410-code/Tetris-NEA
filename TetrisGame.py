from settings import *
import random

import pygame.freetype as ft
import pygame as pg

from Tetromino import Tetromino, Block  # REQUIRED (your code uses these names)


class Text:
    """
    Practice-mode HUD (single board).
    In multiplayer modes we will draw per-board labels separately in the match controller.
    """
    def __init__(self, app):
        self.app = app
        try:
            self.font = ft.Font(FONT_PATH)
            self.using_freetype = True
        except (FileNotFoundError, OSError):
            # Fallback to regular pygame font
            self.font = None
            self.using_freetype = False

    def draw(self):
        if self.using_freetype and self.font:
            # Use FreeType font
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.595, WIN_W * 0.02),
                text='TETRIS',
                fgcolor='white',
                size=TILE_SIZE * 1.65
            )
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.65, WIN_H * 0.22),
                text='NEXT',
                fgcolor='white',
                size=TILE_SIZE * 1.4
            )
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.64, WIN_H * 0.67),
                text='SCORE',
                fgcolor='white',
                size=TILE_SIZE * 1.4
            )
            self.font.render_to(
                self.app.screen,
                (WIN_W * 0.64, WIN_H * 0.8),
                text=f'{self.app.tetris.score}',
                fgcolor='white',
                size=TILE_SIZE * 1.8
            )
        else:
            # Use regular pygame font as fallback
            fallback_font_large = pg.font.Font(None, int(TILE_SIZE * 1.65))
            fallback_font_medium = pg.font.Font(None, int(TILE_SIZE * 1.4))
            fallback_font_score = pg.font.Font(None, int(TILE_SIZE * 1.8))
            
            tetris_text = fallback_font_large.render('TETRIS', True, 'white')
            next_text = fallback_font_medium.render('NEXT', True, 'white')
            score_label = fallback_font_medium.render('SCORE', True, 'white')
            score_value = fallback_font_score.render(f'{self.app.tetris.score}', True, 'white')
            
            self.app.screen.blit(tetris_text, (WIN_W * 0.595, WIN_W * 0.02))
            self.app.screen.blit(next_text, (WIN_W * 0.65, WIN_H * 0.22))
            self.app.screen.blit(score_label, (WIN_W * 0.64, WIN_H * 0.67))
            self.app.screen.blit(score_value, (WIN_W * 0.64, WIN_H * 0.8))


class Tetris:
    def __init__(self, app, offset_tiles=None, is_simulation=False, random_seed=None):
        self.app = app
        self.is_simulation = is_simulation

        # Per-board random number generator (prevents boards sharing the same sequence)
        # If random_seed is None, Python uses a system-based seed.
        self.random_generator = random.Random(random_seed)

        # Sprite group for real games only
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

        # Initialise game field
        self.field_array = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

        # Game state
        self.speed_up = False
        self.score = 0
        self.full_lines = 0
        self.lines_cleared = 0
        self.game_over_flag = False

        # Standard Tetris-like scoring (your existing mapping)
        self.points_per_line = {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}

        # Create tetrominoes (pass RNG so each board is independent)
        self.tetromino = Tetromino(self, current_shape=True, rng=self.random_generator)
        self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)

    def get_score(self):
        self.score += self.points_per_line[self.full_lines]
        self.lines_cleared += self.full_lines
        self.full_lines = 0

    def check_full_line(self):
        target_row_index = FIELD_H - 1

        for current_row_index in range(FIELD_H - 1, -1, -1):
            row_is_full = True
            for column_index in range(FIELD_W):
                if not self.field_array[current_row_index][column_index]:
                    row_is_full = False
                    break

            if not row_is_full:
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

    def put_tetromino_blocks_in_array(self):
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if 0 <= grid_x < FIELD_W and 0 <= grid_y < FIELD_H:
                self.field_array[grid_y][grid_x] = block

    def check_game_over(self):
        # Check if spawn area is blocked
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if grid_y <= 1 and self.field_array[grid_y][grid_x]:
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
                block.pos = vec(
                    block.pos.x - NEXT_TETROMINO_POS.x + INIT_POS_OFFSET.x,
                    block.pos.y - NEXT_TETROMINO_POS.y + INIT_POS_OFFSET.y
                )
                block.is_next_piece = False

            # Generate new next piece (use same RNG)
            self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)
            self.tetromino.landing = False

    # -----------------------------
    # Controls (Practice mode + Match mode)
    # -----------------------------
    def control(self, pressed_key):
        """Practice mode controls (arrow keys)."""
        if pressed_key == pg.K_LEFT:
            self.tetromino.move(direction='left')
        elif pressed_key == pg.K_RIGHT:
            self.tetromino.move(direction='right')
        elif pressed_key == pg.K_UP:
            self.tetromino.rotate()
        elif pressed_key == pg.K_DOWN:
            self.speed_up = True

    def control_action(self, action_name):
        """Match mode controls (action-based)."""
        if action_name == "left":
            self.tetromino.move(direction='left')
        elif action_name == "right":
            self.tetromino.move(direction='right')
        elif action_name == "rotate":
            self.tetromino.rotate()
        elif action_name == "down":
            self.speed_up = True

    # -----------------------------
    # Rendering / update
    # -----------------------------
    def draw_grid(self):
        if self.is_simulation:
            return

        for grid_x in range(FIELD_W):
            for grid_y in range(FIELD_H):
                pg.draw.rect(
                    self.app.screen,
                    (50, 70, 110),
                    (
                        (grid_x + self.offset_tiles.x) * TILE_SIZE,
                        (grid_y + self.offset_tiles.y) * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE
                    ),
                    1
                )

    def update(self):
        if self.game_over_flag:
            return

        animation_trigger = self.app.fast_animation_trigger if self.speed_up else self.app.animation_trigger

        if animation_trigger:
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

    # -----------------------------
    # AI support (kept for Medium CPU)
    # -----------------------------
    def get_board_matrix(self):
        board_matrix = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

        # Add landed blocks
        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                if self.field_array[grid_y][grid_x]:
                    board_matrix[grid_y][grid_x] = 1

        # Add current falling piece
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if 0 <= grid_x < FIELD_W and 0 <= grid_y < FIELD_H:
                board_matrix[grid_y][grid_x] = 1

        return board_matrix

    def clone(self):
        """Creates a simulation clone (used for CPU Medium move evaluation)."""

        class DummyApp:
            def __init__(self, images):
                self.images = images
                self.animation_trigger = True
                self.fast_animation_trigger = False

        simulation_clone = Tetris(
            DummyApp(self.images),
            offset_tiles=self.offset_tiles,
            is_simulation=True,
            random_seed=None  # seed not important for move simulation
        )

        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                simulation_clone.field_array[grid_y][grid_x] = 1 if self.field_array[grid_y][grid_x] else 0

        # Copy game state
        simulation_clone.score = self.score
        simulation_clone.lines_cleared = self.lines_cleared
        simulation_clone.game_over_flag = self.game_over_flag

        # Tetromino clone for simulation
        simulation_clone.tetromino = self._simple_clone_tetromino(self.tetromino, simulation_clone, is_current=True)
        simulation_clone.next_tetromino = self._simple_clone_tetromino(self.next_tetromino, simulation_clone, is_current=False)

        return simulation_clone

    def _simple_clone_tetromino(self, original_tetromino, target_tetris, is_current):
        """Clone simulation that doesn't need to display sprites."""

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
                grid_x, grid_y = int(test_pos.x), int(test_pos.y)
                if grid_x < 0 or grid_x >= FIELD_W or grid_y >= FIELD_H:
                    return True
                if grid_y < 0:
                    return False
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
                if not self.has_collided(new_positions):
                    for i, block in enumerate(self.blocks):
                        block.pos = new_positions[i]

            def has_collided(self, positions):
                for block, test_pos in zip(self.blocks, positions):
                    if block.has_collided(test_pos):
                        return True
                return False

            def move(self, direction):
                if not self.blocks:
                    return

                move_direction_vector = MOVE_DIRECTIONS[direction]
                new_positions = [block.pos + move_direction_vector for block in self.blocks]

                if not self.has_collided(new_positions):
                    for block in self.blocks:
                        block.pos += move_direction_vector
                elif direction == 'down':
                    self.landing = True

            def update(self):
                self.move('down')

        blocks_data = []
        for block in original_tetromino.blocks:
            if block.is_next_piece:
                original_relative_pos = block.pos - NEXT_TETROMINO_POS
            else:
                original_relative_pos = block.pos - INIT_POS_OFFSET
            blocks_data.append((original_relative_pos, block.is_next_piece))

        return SimpleTetromino(original_tetromino.shape, blocks_data, is_current)

    def get_possible_moves(self):
        """Gets all possible moves for the current tetromino (used by CPU Medium)."""
        possible_moves = []
        simulation_game = self.clone()

        for rotation_count in range(4):
            rotated_simulation = simulation_game.clone()

            for _ in range(rotation_count):
                rotated_simulation.tetromino.rotate()

            for target_x in range(FIELD_W):
                test_simulation = rotated_simulation.clone()

                current_x = int(test_simulation.tetromino.blocks[0].pos.x)
                horizontal_shift = target_x - current_x

                can_move_horizontally = True
                for _ in range(abs(horizontal_shift)):
                    step_direction = vec(1 if horizontal_shift > 0 else -1, 0)
                    new_positions = [block.pos + step_direction for block in test_simulation.tetromino.blocks]

                    if test_simulation.tetromino.has_collided(new_positions):
                        can_move_horizontally = False
                        break

                    for block in test_simulation.tetromino.blocks:
                        block.pos += step_direction

                if not can_move_horizontally:
                    continue

                # Hard drop
                while True:
                    new_positions = [block.pos + vec(0, 1) for block in test_simulation.tetromino.blocks]
                    if test_simulation.tetromino.has_collided(new_positions):
                        break
                    for block in test_simulation.tetromino.blocks:
                        block.pos.y += 1

                is_valid_move = True
                for block in test_simulation.tetromino.blocks:
                    grid_x, grid_y = int(block.pos.x), int(block.pos.y)
                    if grid_x < 0 or grid_x >= FIELD_W or grid_y < 0 or grid_y >= FIELD_H:
                        is_valid_move = False
                        break

                if is_valid_move:
                    possible_moves.append((rotation_count, target_x))

        return possible_moves

    def apply_ai_move(self, move):
        """Apply CPU-selected move to the board."""
        if not move or self.game_over_flag:
            return

        rotation_count, target_x = move

        for _ in range(rotation_count):
            self.tetromino.rotate()

        current_x = int(self.tetromino.blocks[0].pos.x)
        horizontal_shift = target_x - current_x

        if horizontal_shift != 0:
            step_direction = vec(1 if horizontal_shift > 0 else -1, 0)
            for _ in range(abs(horizontal_shift)):
                new_positions = [block.pos + step_direction for block in self.tetromino.blocks]
                if self.tetromino.has_collided(new_positions):
                    break
                for block in self.tetromino.blocks:
                    block.pos += step_direction

        # Hard drop
        while True:
            new_positions = [block.pos + vec(0, 1) for block in self.tetromino.blocks]
            if self.tetromino.has_collided(new_positions):
                self.tetromino.landing = True
                break
            for block in self.tetromino.blocks:
                block.pos.y += 1

        if self.tetromino.landing:
            self.check_tetromino_landing()