from settings import *
from TetrisGame import Tetris, Text
from leaderboard_manager import get_top_scores, append_solo_score

import sys
import pathlib
import pygame as pg


font_cache = {}
font_warning_shown = False


class App:
    def __init__(self, solo_speed: int = 3, player_name: str = "Player"):
        pg.display.set_caption("Tetris")
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        self.is_solo = True
        self.player_name = player_name
        self.score_saved = False

        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1

        self.animation_trigger = False
        self.fast_animation_trigger = False

        self.images = self.load_sprites()

        self.paused = False
        self.pause_font = pg.font.Font(None, 96)

        self.tetris = Tetris(self, solo_mode=True, solo_speed=solo_speed)
        self.text = Text(self)

        self.set_timer(self.tetris.get_fall_interval_ms())

    def load_sprites(self):
        sprite_paths = [path for path in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if path.is_file()]
        if not sprite_paths:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")
            return []
        loaded_images = [pg.image.load(path).convert_alpha() for path in sprite_paths]
        scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]
        return scaled_images

    def set_timer(self, normal_interval_ms: int):
        pg.time.set_timer(self.normal_tick_event, int(normal_interval_ms))
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMATION_TIME_INTERVAL)

    def set_fall_interval_ms(self, normal_interval_ms: int):
        pg.time.set_timer(self.normal_tick_event, int(normal_interval_ms))

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.tetris.speed_up = False

    def update(self):
        if self.paused:
            self.clock.tick(FPS)
            return

        self.tetris.update()

        if self.tetris.game_over_flag and self.is_solo and not self.score_saved:
            if self.tetris.score > 0:
                append_solo_score(
                    LEADERBOARD_SOLO_CSV,
                    name=self.player_name,
                    score=self.tetris.score,
                    speed=getattr(self.tetris, "manual_speed", 3),
                    level=getattr(self.tetris, "level", 1),
                    lines=self.tetris.lines_cleared,
                )
            self.score_saved = True
            self.is_solo = False

        self.clock.tick(FPS)

    def draw_pause_overlay(self):
        screen_width, screen_height = self.screen.get_size()
        overlay = pg.Surface((screen_width, screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        paused_text = self.pause_font.render("PAUSED", True, (255, 255, 255))
        paused_rect = paused_text.get_rect(center=(screen_width // 2, screen_height // 2))
        self.screen.blit(paused_text, paused_rect)

        hint_text = pg.font.Font(None, 36).render("Press P to resume", True, (220, 220, 220))
        hint_rect = hint_text.get_rect(center=(screen_width // 2, screen_height // 2 + 70))
        self.screen.blit(hint_text, hint_rect)

    def draw(self):
        self.screen.fill(color=BACKGROUND_COLOUR)
        self.tetris.draw()
        self.text.draw()

        if self.paused:
            self.draw_pause_overlay()

        pg.display.flip()

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == PAUSE_KEY_SOLO:
                self.toggle_pause()
                continue

            if self.paused:
                continue

            if event.type == pg.KEYDOWN and not self.tetris.game_over_flag:
                self.tetris.control(event.key)

            if event.type == pg.KEYUP and event.key == pg.K_DOWN:
                self.tetris.speed_up = False

            if event.type == self.normal_tick_event:
                self.animation_trigger = True
            elif event.type == self.fast_tick_event:
                self.fast_animation_trigger = True

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


def get_font(font_size):
    global font_cache, font_warning_shown

    if font_size in font_cache:
        return font_cache[font_size]

    try:
        font = pg.font.Font(FONT_PATH, font_size)
        font_cache[font_size] = font
        return font
    except FileNotFoundError:
        if not font_warning_shown:
            print("Warning: Custom font not found, using default pygame font")
            font_warning_shown = True

        font = pg.font.Font(None, font_size)
        font_cache[font_size] = font
        return font


def make_background(width, height, top_colour, bottom_colour):
    background_surface = pg.Surface((width, height))
    for y_pos in range(height):
        blend_ratio = y_pos / height
        red = int(top_colour[0] * (1 - blend_ratio) + bottom_colour[0] * blend_ratio)
        green = int(top_colour[1] * (1 - blend_ratio) + bottom_colour[1] * blend_ratio)
        blue = int(top_colour[2] * (1 - blend_ratio) + bottom_colour[2] * blend_ratio)
        pg.draw.line(background_surface, (red, green, blue), (0, y_pos), (width, y_pos))
    return background_surface


def draw_button(surface, rect, text, font, is_hovering, base_colour=(70, 130, 180), hover_colour=(100, 160, 210)):
    fill_colour = hover_colour if is_hovering else base_colour

    pg.draw.rect(surface, fill_colour, rect, border_radius=15)
    pg.draw.rect(surface, (255, 255, 255, 100), rect, width=2, border_radius=15)

    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)


class Button:
    def __init__(self, rect, text, font, base_colour=(70, 130, 180), hover_colour=(100, 160, 210)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.base_colour = base_colour
        self.hover_colour = hover_colour
        self.is_hovering = False

    def update(self, mouse_position):
        self.is_hovering = self.rect.collidepoint(mouse_position)

    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.is_hovering, self.base_colour, self.hover_colour)

    def is_clicked(self, mouse_position):
        return self.rect.collidepoint(mouse_position)


class TextInput:
    """Single-line text input box"""
    def __init__(self, centre_pos, width=350, height=50, label="PLAYER"):
        self.rect = pg.Rect(0, 0, width, height)
        self.rect.center = centre_pos
        self.is_active = False
        self.text = ""
        self.label = label

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.is_active = self.rect.collidepoint(event.pos)

        if event.type == pg.KEYDOWN and self.is_active:
            if event.key == pg.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_TAB):
                self.is_active = False
            else:
                if len(self.text) < 15 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface):
        background_colour = (50, 100, 150) if self.is_active else (40, 60, 90)
        pg.draw.rect(surface, background_colour, self.rect, border_radius=8)

        border_colour = (100, 200, 255) if self.is_active else (80, 100, 120)
        border_width = 3 if self.is_active else 2
        pg.draw.rect(surface, border_colour, self.rect, width=border_width, border_radius=8)

        label_font = get_font(20)
        label_surface = label_font.render(self.label, True, (180, 180, 200))
        surface.blit(label_surface, (self.rect.left, self.rect.top - 25))

        value_font = get_font(26)
        display_text = self.text if self.text else "(click to type)"
        text_colour = (255, 255, 255) if self.text else (120, 120, 140)
        value_surface = value_font.render(display_text, True, text_colour)
        surface.blit(value_surface, (self.rect.left + 12, self.rect.centery - 13))


def local_2p_name_entry():
    """Screen to enter player names for 2P local match"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("2 Player - Enter Names")

    background = make_background(1280, 720, (20, 25, 40), (35, 20, 50))

    centre_x = 640

    player1_input = TextInput((centre_x, 280), label="PLAYER 1 NAME")
    player2_input = TextInput((centre_x, 360), label="PLAYER 2 NAME")

    start_button = Button((centre_x - 110, 480, 220, 60), "START MATCH", get_font(36), (50, 160, 80), (70, 190, 110))
    back_button = Button((centre_x - 110, 560, 220, 60), "BACK", get_font(36), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(70)
        title_surface = title_font.render("2 PLAYER LOCAL", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 100))
        screen.blit(title_surface, title_rect)

        instruction_font = get_font(26)
        instruction_surface = instruction_font.render("Enter player names and click START", True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(centre_x, 180))
        screen.blit(instruction_surface, instruction_rect)

        controls_font = get_font(22)
        controls_surface = controls_font.render("Controls: P1=WASD | P2=IJKL", True, (150, 150, 150))
        controls_rect = controls_surface.get_rect(center=(centre_x, 420))
        screen.blit(controls_surface, controls_rect)

        player1_input.draw(screen)
        player2_input.draw(screen)

        start_button.update(mouse_position)
        start_button.draw(screen)

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return None

            player1_input.handle_event(event)
            player2_input.handle_event(event)

            if event.type == pg.MOUSEBUTTONDOWN:
                if start_button.is_clicked(mouse_position):
                    player1_name = player1_input.text.strip() or "Player 1"
                    player2_name = player2_input.text.strip() or "Player 2"
                    return [player1_name, player2_name]
                if back_button.is_clicked(mouse_position):
                    return None

        pg.display.flip()
        clock.tick(60)


def local_3p_name_entry():
    """Screen to enter player names for 3P local match"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("3 Player - Enter Names")

    background = make_background(1280, 720, (20, 25, 40), (35, 20, 50))

    centre_x = 640

    player1_input = TextInput((centre_x, 240), label="PLAYER 1 NAME")
    player2_input = TextInput((centre_x, 320), label="PLAYER 2 NAME")
    player3_input = TextInput((centre_x, 400), label="PLAYER 3 NAME")

    start_button = Button((centre_x - 110, 520, 220, 60), "START MATCH", get_font(36), (50, 160, 80), (70, 190, 110))
    back_button = Button((centre_x - 110, 600, 220, 60), "BACK", get_font(36), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(70)
        title_surface = title_font.render("3 PLAYER LOCAL", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 80))
        screen.blit(title_surface, title_rect)

        instruction_font = get_font(26)
        instruction_surface = instruction_font.render("Enter player names and click START", True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(centre_x, 160))
        screen.blit(instruction_surface, instruction_rect)

        controls_font = get_font(20)
        controls_surface = controls_font.render("Controls: P1=WASD | P2=IJKL | P3=Arrows", True, (150, 150, 150))
        controls_rect = controls_surface.get_rect(center=(centre_x, 470))
        screen.blit(controls_surface, controls_rect)

        player1_input.draw(screen)
        player2_input.draw(screen)
        player3_input.draw(screen)

        start_button.update(mouse_position)
        start_button.draw(screen)

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return None

            player1_input.handle_event(event)
            player2_input.handle_event(event)
            player3_input.handle_event(event)

            if event.type == pg.MOUSEBUTTONDOWN:
                if start_button.is_clicked(mouse_position):
                    player1_name = player1_input.text.strip() or "Player 1"
                    player2_name = player2_input.text.strip() or "Player 2"
                    player3_name = player3_input.text.strip() or "Player 3"
                    return [player1_name, player2_name, player3_name]
                if back_button.is_clicked(mouse_position):
                    return None

        pg.display.flip()
        clock.tick(60)


def local_multiplayer_2p():
    """Launch 2P match with name entry"""
    names = local_2p_name_entry()
    if names:
        from versus import MatchApp
        MatchApp(
            total_players=2,
            cpu_opponents=0,
            cpu_difficulty="medium",
            player_names=names
        ).run()


def local_multiplayer_3p():
    """Launch 3P match with name entry"""
    names = local_3p_name_entry()
    if names:
        from versus import MatchApp
        MatchApp(
            total_players=3,
            cpu_opponents=0,
            cpu_difficulty="medium",
            player_names=names
        ).run()


def speed_selection_menu():
    """Menu to select solo game speed"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Select Speed")

    background = make_background(1280, 720, (20, 20, 40), (40, 20, 60))

    centre_x = 640

    speed_buttons = {}
    button_width, button_height = 250, 70
    first_button_y = 200
    button_spacing = 85

    for speed_value in range(1, 6):
        multiplier = SPEED_SCORE_MULTIPLIERS[speed_value]
        speed_buttons[speed_value] = Button(
            (centre_x - button_width // 2, first_button_y + (speed_value - 1) * button_spacing, button_width, button_height),
            f"SPEED {speed_value} ({multiplier}x)",
            get_font(36),
            (50 + speed_value * 15, 130 - speed_value * 8, 160 - speed_value * 8),
            (70 + speed_value * 15, 150 - speed_value * 8, 180 - speed_value * 8)
        )

    back_button = Button((centre_x - 125, 630, 250, 60), "BACK", get_font(36), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(70)
        title_surface = title_font.render("SELECT SPEED", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 80))
        screen.blit(title_surface, title_rect)

        info_font = get_font(24)
        info_surface = info_font.render("Higher speed = Faster game + Higher score multiplier", True, (200, 200, 200))
        info_rect = info_surface.get_rect(center=(centre_x, 140))
        screen.blit(info_surface, info_rect)

        for button in speed_buttons.values():
            button.update(mouse_position)
            button.draw(screen)

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return None

            if event.type == pg.MOUSEBUTTONDOWN:
                for speed_value, button in speed_buttons.items():
                    if button.is_clicked(mouse_position):
                        return speed_value
                if back_button.is_clicked(mouse_position):
                    return None

        pg.display.flip()
        clock.tick(60)


def name_entry_menu():
    """Enter player name for solo mode"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Enter Your Name")

    background = make_background(1280, 720, (20, 20, 40), (40, 20, 60))

    centre_x = 640

    name_input = TextInput((centre_x, 320), width=400, label="YOUR NAME")

    continue_button = Button((centre_x - 125, 450, 250, 70), "CONTINUE", get_font(40), (50, 160, 80), (70, 190, 110))
    back_button = Button((centre_x - 125, 540, 250, 70), "BACK", get_font(40), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(70)
        title_surface = title_font.render("SOLO MODE", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 140))
        screen.blit(title_surface, title_rect)

        instruction_font = get_font(28)
        instruction_surface = instruction_font.render("Enter your name for the leaderboard", True, (200, 200, 200))
        instruction_rect = instruction_surface.get_rect(center=(centre_x, 220))
        screen.blit(instruction_surface, instruction_rect)

        name_input.draw(screen)

        continue_button.update(mouse_position)
        continue_button.draw(screen)

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return None

            name_input.handle_event(event)

            if event.type == pg.MOUSEBUTTONDOWN:
                if continue_button.is_clicked(mouse_position):
                    return name_input.text.strip() or "Player"
                if back_button.is_clicked(mouse_position):
                    return None

        pg.display.flip()
        clock.tick(60)


def play_solo():
    """Start solo mode with name and speed selection"""
    player_name = name_entry_menu()
    if not player_name:
        return

    speed_value = speed_selection_menu()
    if speed_value:
        App(solo_speed=speed_value, player_name=player_name).run()


def how_to_play_screen():
    """Display how to play instructions"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("How to Play")

    background = make_background(1280, 720, (20, 25, 40), (35, 20, 50))
    back_button = Button((540, 640, 200, 60), "BACK", get_font(36), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(60)
        title_surface = title_font.render("HOW TO PLAY TETRIS", True, (255, 215, 100))
        screen.blit(title_surface, (300, 40))

        instruction_font = get_font(24)
        instructions = [
            " Move and rotate falling pieces to complete full horizontal lines.",
            " Completed lines disappear and the above drops down.",
            " Clear more lines at once for more points!",
            "",
            "SCORING (base with no multipliers):",
            "  SINGLE = 100, DOUBLE = 300, TRIPLE = 700, TETRIS! = 1500",
            "",
            "LEVELS:",
            "  Start at Level 1. Every 10 lines cleared increases level by 1.",
            "  Higher levels increase fall speed.",
            "",
            "SOLO SPEED:",
            "  Choose Speed 1–5 from the Solo Setup menu.",
            "  Higher speed increases your score multiplier (up to x3.0).",
            "",
            "PIECES:",
            "I piece O piece T piece S piece Z piece J piece L piece",
        ]

        y_pos = 140
        for line in instructions:
            text_surface = instruction_font.render(line, True, (220, 220, 220))
            screen.blit(text_surface, (150, y_pos))
            y_pos += 32

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return
            if event.type == pg.MOUSEBUTTONDOWN and back_button.is_clicked(mouse_position):
                return

        pg.display.flip()
        clock.tick(60)


def controls_screen():
    """Display control schemes"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Controls")

    background = make_background(1280, 720, (20, 25, 40), (35, 20, 50))
    back_button = Button((540, 640, 200, 60), "BACK", get_font(36), (80, 80, 80), (110, 110, 110))

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(60)
        title_surface = title_font.render("CONTROLS", True, (255, 215, 100))
        screen.blit(title_surface, (480, 40))

        header_font = get_font(32)
        text_font = get_font(24)

        y_pos = 130

        solo_header_surface = header_font.render("SOLO MODE:", True, (100, 200, 255))
        screen.blit(solo_header_surface, (150, y_pos))
        y_pos += 50

        solo_controls = [
            "Arrow Keys: Move Left/Right/Down",
            "Up Arrow: Rotate piece",
            "P: Pause game"
        ]
        for control_line in solo_controls:
            line_surface = text_font.render(control_line, True, (220, 220, 220))
            screen.blit(line_surface, (150, y_pos))
            y_pos += 35

        y_pos += 30

        multi_header_surface = header_font.render("MULTIPLAYER:", True, (100, 200, 255))
        screen.blit(multi_header_surface, (150, y_pos))
        y_pos += 50

        multi_controls = [
            "Player 1: W=Rotate, A=Left, S=Down, D=Right",
            "Player 2: I=Rotate, J=Left, K=Down, L=Right",
            "Player 3: Arrow Keys (Up=Rotate, others as labelled)",
            "Press P to pause match"
        ]
        for control_line in multi_controls:
            line_surface = text_font.render(control_line, True, (220, 220, 220))
            screen.blit(line_surface, (150, y_pos))
            y_pos += 35

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return
            if event.type == pg.MOUSEBUTTONDOWN and back_button.is_clicked(mouse_position):
                return

        pg.display.flip()
        clock.tick(60)


def leaderboard_screen():
    """Display top 5 scores from each category"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Leaderboards")

    background = make_background(1280, 720, (20, 25, 40), (35, 20, 50))

    tab_buttons = {
        'solo': Button((100, 50, 200, 50), "SOLO", get_font(28), (60, 90, 130), (90, 120, 160)),
        '2p': Button((350, 50, 200, 50), "2 PLAYER", get_font(28), (60, 90, 130), (90, 120, 160)),
        '3p': Button((600, 50, 200, 50), "3 PLAYER", get_font(28), (60, 90, 130), (90, 120, 160)),
        'cpu': Button((850, 50, 200, 50), "VS CPU", get_font(28), (60, 90, 130), (90, 120, 160)),
    }

    back_button = Button((1050, 650, 200, 50), "BACK", get_font(32), (80, 80, 80), (110, 110, 110))

    current_tab = 'solo'
    clock = pg.time.Clock()

    csv_files = {
        'solo': LEADERBOARD_SOLO_CSV,
        '2p': LEADERBOARD_2P_CSV,
        '3p': LEADERBOARD_3P_CSV,
        'cpu': LEADERBOARD_CPU_CSV
    }

    tab_titles = {
        'solo': "TOP 5 - SOLO MODE",
        '2p': "TOP 5 - 2 PLAYER",
        '3p': "TOP 5 - 3 PLAYER",
        'cpu': "TOP 5 - VS CPU"
    }

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        for tab_name, tab_button in tab_buttons.items():
            if tab_name == current_tab:
                tab_button.base_colour = (60, 180, 80)
                tab_button.hover_colour = (80, 210, 110)
            else:
                tab_button.base_colour = (60, 90, 130)
                tab_button.hover_colour = (90, 120, 160)

            tab_button.update(mouse_position)
            tab_button.draw(screen)

        scores = get_top_scores(csv_files[current_tab], 5)

        title_font = get_font(48)
        title_surface = title_font.render(tab_titles[current_tab], True, (255, 215, 100))
        screen.blit(title_surface, (350, 130))

        header_font = get_font(32)
        screen.blit(header_font.render("RANK", True, (200, 200, 200)), (300, 200))
        screen.blit(header_font.render("NAME", True, (200, 200, 200)), (450, 200))
        screen.blit(header_font.render("SCORE", True, (200, 200, 200)), (750, 200))

        entry_font = get_font(28)
        y_start = 250

        for entry in scores:
            rank_surface = entry_font.render(f"#{entry['rank']}", True, (255, 255, 255))
            name_surface = entry_font.render(entry['name'], True, (255, 255, 255))
            score_surface = entry_font.render(str(entry['score']), True, (255, 255, 100))

            y_pos = y_start + (entry['rank'] - 1) * 60
            screen.blit(rank_surface, (300, y_pos))
            screen.blit(name_surface, (450, y_pos))
            screen.blit(score_surface, (750, y_pos))

        if not scores:
            no_data_font = get_font(36)
            no_data_surface = no_data_font.render("No scores yet!", True, (150, 150, 150))
            screen.blit(no_data_surface, (500, 350))

        back_button.update(mouse_position)
        back_button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return

            if event.type == pg.MOUSEBUTTONDOWN:
                for tab_name, tab_button in tab_buttons.items():
                    if tab_button.is_clicked(mouse_position):
                        current_tab = tab_name
                if back_button.is_clicked(mouse_position):
                    return

        pg.display.flip()
        clock.tick(60)


def main_menu():
    """Main menu with reorganised layout"""
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Tetris - Main Menu")

    background = make_background(1280, 720, (20, 20, 40), (40, 20, 60))

    centre_x = 640
    button_width = 400
    button_height = 65
    first_button_y = 240
    button_spacing = 85

    menu_buttons = {
        'practice': Button(
            (centre_x - button_width // 2, first_button_y, button_width, button_height),
            "PRACTICE (SOLO)", get_font(40), (50, 130, 160), (70, 160, 200)
        ),
        'local_2p': Button(
            (centre_x - button_width // 2, first_button_y + button_spacing, button_width, button_height),
            "LOCAL 2 PLAYER", get_font(40), (140, 80, 150), (170, 110, 180)
        ),
        'local_3p': Button(
            (centre_x - button_width // 2, first_button_y + button_spacing * 2, button_width, button_height),
            "LOCAL 3 PLAYER", get_font(40), (140, 80, 150), (170, 110, 180)
        ),
        'vs_cpu': Button(
            (centre_x - button_width // 2, first_button_y + button_spacing * 3, button_width, button_height),
            "VS CPU", get_font(40), (180, 60, 60), (210, 90, 90)
        ),
        'quit': Button(
            (1100, 30, 150, 50),
            "QUIT", get_font(32), (180, 60, 60), (210, 90, 90)
        ),
        'leaderboard': Button(
            (480, 630, 160, 50),
            "LEADERBOARD", get_font(24), (100, 60, 140), (130, 90, 170)
        ),
        'how_to_play': Button(
            (660, 630, 160, 50),
            "HOW TO PLAY", get_font(24), (60, 140, 100), (90, 170, 130)
        ),
        'controls': Button(
            (840, 630, 160, 50),
            "CONTROLS", get_font(24), (60, 100, 140), (90, 130, 170)
        ),
    }

    clock = pg.time.Clock()

    while True:
        mouse_position = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(100)
        title_surface = title_font.render("TETRIS", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(640, 110))
        screen.blit(title_surface, title_rect)

        for button in menu_buttons.values():
            button.update(mouse_position)
            button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if menu_buttons['practice'].is_clicked(mouse_position):
                    play_solo()
                elif menu_buttons['local_2p'].is_clicked(mouse_position):
                    local_multiplayer_2p()
                elif menu_buttons['local_3p'].is_clicked(mouse_position):
                    local_multiplayer_3p()
                elif menu_buttons['vs_cpu'].is_clicked(mouse_position):
                    import versus_menu
                    versus_menu.versus_menu()
                elif menu_buttons['leaderboard'].is_clicked(mouse_position):
                    leaderboard_screen()
                elif menu_buttons['how_to_play'].is_clicked(mouse_position):
                    how_to_play_screen()
                elif menu_buttons['controls'].is_clicked(mouse_position):
                    controls_screen()
                elif menu_buttons['quit'].is_clicked(mouse_position):
                    pg.quit()
                    sys.exit()

        pg.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    pg.init()
    main_menu()
