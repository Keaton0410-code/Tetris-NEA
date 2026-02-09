from settings import *
from Tetromino import Tetromino, Block

import random
import pygame.freetype as ft
import pygame as pg


class ScorePopup:
    def __init__(self, tetris, text: str, tile_pos: vec, colour=(255, 240, 140)):
        self.tetris = tetris
        self.text = text
        self.tile_pos = vec(tile_pos)
        self.colour = colour
        self.life_frames = 60
        self.age_frames = 0

    def update(self):
        self.age_frames += 1
        self.tile_pos.y -= 0.01
        return self.age_frames < self.life_frames

    def draw(self, surface, font: pg.font.Font):
        alpha = max(0, 255 - int(255 * (self.age_frames / self.life_frames)))
        rgb = (self.colour[0], self.colour[1], self.colour[2])

        text_surface = font.render(self.text, True, rgb).convert_alpha()
        text_surface.set_alpha(alpha)

        pixel_x = int((self.tile_pos.x + self.tetris.offset_tiles.x) * TILE_SIZE)
        pixel_y = int((self.tile_pos.y + self.tetris.offset_tiles.y) * TILE_SIZE)
        surface.blit(text_surface, (pixel_x, pixel_y))


class Text:
    def __init__(self, app):
        self.app = app
        try:
            self.font = ft.Font(FONT_PATH)
            self.using_freetype = True
        except (FileNotFoundError, OSError):
            self.font = None
            self.using_freetype = False

        self.fallback_title = pg.font.Font(None, int(TILE_SIZE * 1.65))
        self.fallback_mid = pg.font.Font(None, int(TILE_SIZE * 1.2))
        self.fallback_big = pg.font.Font(None, int(TILE_SIZE * 1.8))

    def draw(self):
        tetris_game = self.app.tetris

        title_pos = (WIN_W * 0.595, WIN_W * 0.02)
        next_pos = (WIN_W * 0.65, WIN_H * 0.22)
        score_label_pos = (WIN_W * 0.64, WIN_H * 0.67)
        score_value_pos = (WIN_W * 0.64, WIN_H * 0.78)
        speed_pos = (WIN_W * 0.64, WIN_H * 0.88)
        level_pos = (WIN_W * 0.64, WIN_H * 0.94)

        if self.using_freetype and self.font:
            self.font.render_to(self.app.screen, title_pos, text="TETRIS", fgcolor="white", size=TILE_SIZE * 1.65)
            self.font.render_to(self.app.screen, next_pos, text="NEXT", fgcolor="white", size=TILE_SIZE * 1.4)

            self.font.render_to(self.app.screen, score_label_pos, text="SCORE", fgcolor="white", size=TILE_SIZE * 1.2)
            self.font.render_to(
                self.app.screen, score_value_pos, text=f"{tetris_game.score}", fgcolor="white", size=TILE_SIZE * 1.6
            )

            if getattr(self.app, "is_solo", False):
                self.font.render_to(
                    self.app.screen,
                    speed_pos,
                    text=f"SPEED: {tetris_game.manual_speed}  x{tetris_game.speed_multiplier:.1f}",
                    fgcolor="white",
                    size=TILE_SIZE * 0.9,
                )
                self.font.render_to(
                    self.app.screen,
                    level_pos,
                    text=f"LEVEL: {tetris_game.level}",
                    fgcolor="white",
                    size=TILE_SIZE * 0.9,
                )
        else:
            self.app.screen.blit(self.fallback_title.render("TETRIS", True, "white"), title_pos)
            self.app.screen.blit(self.fallback_mid.render("NEXT", True, "white"), next_pos)

            self.app.screen.blit(self.fallback_mid.render("SCORE", True, "white"), score_label_pos)
            self.app.screen.blit(self.fallback_big.render(f"{tetris_game.score}", True, "white"), score_value_pos)

            if getattr(self.app, "is_solo", False):
                self.app.screen.blit(
                    self.fallback_mid.render(
                        f"SPEED: {tetris_game.manual_speed}  x{tetris_game.speed_multiplier:.1f}", True, "white"
                    ),
                    speed_pos,
                )
                self.app.screen.blit(self.fallback_mid.render(f"LEVEL: {tetris_game.level}", True, "white"), level_pos)


class Tetris:
    def __init__(self, app, offset_tiles=None, is_simulation=False, random_seed=None, solo_mode=False, solo_speed=3):
        self.app = app
        self.is_simulation = is_simulation
        self.solo_mode = bool(solo_mode) and (not is_simulation)

        self.random_generator = random.Random(random_seed)

        if not is_simulation:
            self.sprite_group = pg.sprite.Group()
        else:
            self.sprite_group = None

        self.offset_tiles = offset_tiles if offset_tiles is not None else vec(0, 0)
        self.images = getattr(app, "images", [])

        self.field_array = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]

        self.speed_up = False
        self.score = 0
        self.full_lines = 0
        self.lines_cleared = 0
        self.game_over_flag = False

        self.manual_speed = max(1, min(5, int(solo_speed)))
        self.speed_multiplier = SPEED_SCORE_MULTIPLIERS[self.manual_speed]
        self.level = LEVEL_START

        self.points_per_line = {0: 0, 1: 100, 2: 300, 3: 700, 4: 1500}

        self.popups = []
        self.popup_font = pg.font.Font(None, 42)

        self.tetromino = Tetromino(self, current_shape=True, rng=self.random_generator)
        self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)

        if self.solo_mode and hasattr(self.app, "set_fall_interval_ms"):
            self.app.set_fall_interval_ms(self.get_fall_interval_ms())

    def get_fall_interval_ms(self) -> int:
        if not self.solo_mode:
            return ANIMATION_TIME_INTERVAL
        return combined_fall_interval_ms(self.manual_speed, self.level)

    def get_score(self):
        if self.full_lines <= 0:
            self.full_lines = 0
            return

        base_points = self.points_per_line[self.full_lines]
        gained_points = int(base_points * (self.speed_multiplier if self.solo_mode else 1.0))
        self.score += gained_points
        self.lines_cleared += self.full_lines

        phrase = LINE_CLEAR_PHRASES.get(self.full_lines, "")
        popup_text = f"+{gained_points}"
        if phrase:
            popup_text = f"{popup_text}  {phrase}"

        popup_tile = vec(FIELD_W // 2 - 1, FIELD_H // 2)
        self.popups.append(ScorePopup(self, popup_text, popup_tile))

        self.full_lines = 0

        if self.solo_mode:
            target_level = LEVEL_START + (self.lines_cleared // LINES_PER_LEVEL)
            if target_level != self.level:
                self.level = target_level
                if hasattr(self.app, "set_fall_interval_ms"):
                    self.app.set_fall_interval_ms(self.get_fall_interval_ms())

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

    def lock_piece(self):
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if 0 <= grid_x < FIELD_W and 0 <= grid_y < FIELD_H:
                self.field_array[grid_y][grid_x] = block

    def check_game_over(self):
        for block in self.tetromino.blocks:
            grid_x, grid_y = int(block.pos.x), int(block.pos.y)
            if grid_y <= 1 and self.field_array[grid_y][grid_x]:
                return True
        return False

    def check_landing(self):
        if self.tetromino.landing:
            self.lock_piece()

            if self.check_game_over():
                self.game_over_flag = True
                return

            self.check_full_line()
            self.get_score()

            self.speed_up = False

            self.tetromino = self.next_tetromino
            self.tetromino.current_shape = True

            for block in self.tetromino.blocks:
                block.pos = vec(
                    block.pos.x - NEXT_TETROMINO_POS.x + INIT_POS_OFFSET.x,
                    block.pos.y - NEXT_TETROMINO_POS.y + INIT_POS_OFFSET.y,
                )
                block.is_next_piece = False

            self.next_tetromino = Tetromino(self, current_shape=False, rng=self.random_generator)
            self.tetromino.landing = False

    def control(self, pressed_key):
        if pressed_key == pg.K_LEFT:
            self.tetromino.move(direction="left")
        elif pressed_key == pg.K_RIGHT:
            self.tetromino.move(direction="right")
        elif pressed_key == pg.K_UP:
            self.tetromino.rotate()
        elif pressed_key == pg.K_DOWN:
            self.speed_up = True

    def handle_action(self, action_name):
        if action_name == "left":
            self.tetromino.move(direction="left")
        elif action_name == "right":
            self.tetromino.move(direction="right")
        elif action_name == "rotate":
            self.tetromino.rotate()
        elif action_name == "down":
            self.speed_up = True

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
                        TILE_SIZE,
                    ),
                    1,
                )

    def update(self):
        if self.game_over_flag:
            return

        self.popups = [p for p in self.popups if p.update()]

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

        for popup in self.popups:
            popup.draw(self.app.screen, self.popup_font)

    def get_board(self):
        board_matrix = [[0 for _ in range(FIELD_W)] for _ in range(FIELD_H)]
        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                if self.field_array[grid_y][grid_x]:
                    board_matrix[grid_y][grid_x] = 1
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

        simulation = Tetris(DummyApp(self.images), offset_tiles=self.offset_tiles, is_simulation=True, random_seed=None)

        for grid_y in range(FIELD_H):
            for grid_x in range(FIELD_W):
                simulation.field_array[grid_y][grid_x] = 1 if self.field_array[grid_y][grid_x] else 0

        simulation.score = self.score
        simulation.lines_cleared = self.lines_cleared
        simulation.game_over_flag = self.game_over_flag

        simulation.tetromino = self.clone_tetromino(self.tetromino, simulation, is_current=True)
        simulation.next_tetromino = self.clone_tetromino(self.next_tetromino, simulation, is_current=False)
        return simulation

    def clone_tetromino(self, original_tetromino, target_tetris, is_current):
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
                move_vector = MOVE_DIRECTIONS[direction]
                new_positions = [block.pos + move_vector for block in self.blocks]
                if not self.has_collided(new_positions):
                    for block in self.blocks:
                        block.pos += move_vector
                elif direction == "down":
                    self.landing = True

            def update(self):
                self.move("down")

        blocks_data = []
        for block in original_tetromino.blocks:
            if block.is_next_piece:
                relative_pos = block.pos - NEXT_TETROMINO_POS
            else:
                relative_pos = block.pos - INIT_POS_OFFSET
            blocks_data.append((relative_pos, block.is_next_piece))

        return SimpleTetromino(original_tetromino.shape, blocks_data, is_current)

    def get_possible_moves(self):
        possible_moves = []
        base_simulation = self.clone()

        for rotation_count in range(4):
            rotated_simulation = base_simulation.clone()
            for _ in range(rotation_count):
                rotated_simulation.tetromino.rotate()

            for target_x in range(FIELD_W):
                test_simulation = rotated_simulation.clone()

                current_x = int(test_simulation.tetromino.blocks[0].pos.x)
                horizontal_shift = target_x - current_x

                can_move_horizontally = True
                for _ in range(abs(horizontal_shift)):
                    step = vec(1 if horizontal_shift > 0 else -1, 0)
                    new_positions = [block.pos + step for block in test_simulation.tetromino.blocks]
                    if test_simulation.tetromino.has_collided(new_positions):
                        can_move_horizontally = False
                        break
                    for block in test_simulation.tetromino.blocks:
                        block.pos += step
                if not can_move_horizontally:
                    continue

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
        if not move or self.game_over_flag:
            return

        rotation_count, target_x = move
        for _ in range(rotation_count):
            self.tetromino.rotate()

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

        while True:
            new_positions = [block.pos + vec(0, 1) for block in self.tetromino.blocks]
            if self.tetromino.has_collided(new_positions):
                self.tetromino.landing = True
                break
            for block in self.tetromino.blocks:
                block.pos.y += 1

        if self.tetromino.landing:
            self.check_landing()