from settings import *
from TetrisGame import Tetris, Text
from leaderboard_manager import get_top_scores, append_solo_score

import sys
import pathlib
import pygame as pg


_font_cache = {}
_font_warning_shown = False


class App:
    def __init__(self, solo_speed: int = 3, player_name: str = "Player"):
        pg.display.set_caption("Tetris")
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        self.is_solo = True
        self.player_name = player_name

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
        sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if item.is_file()]
        if not sprite_files:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")
            return []
        loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
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
        if not self.paused:
            self.tetris.update()
        self.clock.tick(FPS)

    def draw_pause_overlay(self):
        screen_width, screen_height = self.screen.get_size()
        overlay = pg.Surface((screen_width, screen_height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        paused_text = self.pause_font.render("PAUSED", True, (255, 255, 255))
        paused_rect = paused_text.get_rect(center=(screen_width // 2, screen_height // 2))
        self.screen.blit(paused_text, paused_rect)

        hint_font = pg.font.Font(None, 36)
        hint_text = hint_font.render("Press P to resume", True, (220, 220, 220))
        hint_rect = hint_text.get_rect(center=(screen_width // 2, screen_height // 2 + 70))
        self.screen.blit(hint_text, hint_rect)

    def draw(self):
        self.screen.fill(BACKGROUND_COLOUR)
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

            if self.paused:
                continue

            if event.type == pg.KEYDOWN:
                self.tetris.control(event.key)

            elif event.type == pg.KEYUP:
                if event.key == pg.K_DOWN:
                    self.tetris.speed_up = False

            elif event.type == self.normal_tick_event:
                self.animation_trigger = True

            elif event.type == self.fast_tick_event:
                self.fast_animation_trigger = True

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


def get_font(font_size):
    global _font_cache, _font_warning_shown
    if font_size in _font_cache:
        return _font_cache[font_size]

    try:
        font = pg.font.Font(FONT_PATH, font_size)
        _font_cache[font_size] = font
        return font
    except FileNotFoundError:
        if not _font_warning_shown:
            print("Warning: Custom font not found, using default pygame font")
            _font_warning_shown = True
        font = pg.font.Font(None, font_size)
        _font_cache[font_size] = font
        return font


def make_background(width, height, top_colour, bottom_colour):
    surface = pg.Surface((width, height))
    for y in range(height):
        blend_ratio = y / height
        red = int(top_colour[0] * (1 - blend_ratio) + bottom_colour[0] * blend_ratio)
        green = int(top_colour[1] * (1 - blend_ratio) + bottom_colour[1] * blend_ratio)
        blue = int(top_colour[2] * (1 - blend_ratio) + bottom_colour[2] * blend_ratio)
        pg.draw.line(surface, (red, green, blue), (0, y), (width, y))
    return surface


def draw_button(surface, rect, text, font, is_hovering, base_colour=(70, 130, 180), hover_colour=(100, 160, 210)):
    button_colour = hover_colour if is_hovering else base_colour
    pg.draw.rect(surface, button_colour, rect, border_radius=15)
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

    def update(self, mouse_pos):
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.is_hovering, self.base_colour, self.hover_colour)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


def practice_menu():
    screen_width, screen_height = 1280, 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Tetris - Solo Setup")
    background = make_background(screen_width, screen_height, (20, 20, 40), (40, 20, 60))
    clock = pg.time.Clock()

    button_width = 160
    button_height = 60
    centre_x = screen_width // 2
    start_y = 260
    gap = 20

    selected_speed = 3

    speed_buttons = []
    for speed_value in range(1, 6):
        x_pos = centre_x - (5 * button_width + 4 * gap) // 2 + (speed_value - 1) * (button_width + gap)
        speed_buttons.append(
            Button(
                (x_pos, start_y, button_width, button_height),
                f"SPEED {speed_value}",
                get_font(28),
                (60, 100, 140),
                (90, 140, 190),
            )
        )

    start_button = Button((centre_x - 210, 520, 200, 60), "START", get_font(40), (50, 130, 160), (70, 160, 200))
    back_button = Button((centre_x + 10, 520, 200, 60), "BACK", get_font(40), (80, 80, 80), (110, 110, 110))

    name_input = {"active": False, "text": "Player"}

    def draw_name_box():
        box_rect = pg.Rect(0, 0, 420, 55)
        box_rect.center = (centre_x, 420)

        box_colour = (60, 90, 130) if name_input["active"] else (40, 60, 90)
        pg.draw.rect(screen, box_colour, box_rect, border_radius=12)
        pg.draw.rect(screen, (120, 150, 200), box_rect, width=2, border_radius=12)

        label_surface = get_font(18).render("NAME (click to edit)", True, (180, 180, 200))
        screen.blit(label_surface, (box_rect.left, box_rect.top - 22))

        shown = name_input["text"] if name_input["text"] else ""
        text_surface = get_font(28).render(shown, True, (255, 255, 255))
        screen.blit(text_surface, (box_rect.left + 12, box_rect.centery - 14))
        return box_rect

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(70)
        title_surface = title_font.render("SOLO SETUP", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 110))
        screen.blit(title_surface, title_rect)

        subtitle_surface = get_font(26).render("Select your speed (affects score multiplier)", True, (210, 210, 230))
        screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(centre_x, 200)))

        for button in speed_buttons + [start_button, back_button]:
            button.update(mouse_pos)
            button.draw(screen)

        name_rect = draw_name_box()

        for speed_value, button in enumerate(speed_buttons, start=1):
            if speed_value == selected_speed:
                pg.draw.rect(screen, (255, 215, 120), button.rect.inflate(6, 6), width=3, border_radius=16)

        multiplier = SPEED_SCORE_MULTIPLIERS[selected_speed]
        hint_surface = get_font(24).render(f"Multiplier: x{multiplier:.1f}   |   Pause: P", True, (200, 200, 220))
        screen.blit(hint_surface, hint_surface.get_rect(center=(centre_x, 350)))

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return None

            if event.type == pg.MOUSEBUTTONDOWN:
                name_input["active"] = name_rect.collidepoint(event.pos)

                for speed_value, button in enumerate(speed_buttons, start=1):
                    if button.is_clicked(mouse_pos):
                        selected_speed = speed_value

                if start_button.is_clicked(mouse_pos):
                    player_name = name_input["text"].strip() or "Player"
                    return (selected_speed, player_name)

                if back_button.is_clicked(mouse_pos):
                    return None

            if event.type == pg.KEYDOWN and name_input["active"]:
                if event.key == pg.K_BACKSPACE:
                    name_input["text"] = name_input["text"][:-1]
                elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                    name_input["active"] = False
                else:
                    if len(name_input["text"]) < 15 and event.unicode.isprintable():
                        name_input["text"] += event.unicode

        pg.display.flip()
        clock.tick(60)


def leaderboard_screen():
    screen_width, screen_height = 1280, 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Leaderboards")
    background = make_background(screen_width, screen_height, (20, 25, 40), (35, 20, 50))
    clock = pg.time.Clock()

    tabs = [
        ("SOLO", LEADERBOARD_SOLO_CSV),
        ("2P", LEADERBOARD_2P_CSV),
        ("3P", LEADERBOARD_3P_CSV),
        ("VS CPU", LEADERBOARD_CPU_CSV),
    ]
    active_tab_index = 0

    tab_buttons = []
    start_x = 200
    for tab_index, (label, _) in enumerate(tabs):
        tab_buttons.append(
            Button((start_x + tab_index * 220, 140, 200, 55), label, get_font(30), (60, 90, 130), (90, 130, 170))
        )

    back_button = Button((40, 40, 160, 50), "BACK", get_font(32), (80, 80, 80), (110, 110, 110))

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_surface = get_font(70).render("LEADERBOARDS", True, (255, 215, 120))
        title_rect = title_surface.get_rect(center=(screen_width // 2, 70))
        screen.blit(title_surface, title_rect)

        for tab_index, button in enumerate(tab_buttons):
            button.update(mouse_pos)
            button.draw(screen)
            if tab_index == active_tab_index:
                pg.draw.rect(screen, (255, 215, 120), button.rect.inflate(6, 6), width=3, border_radius=16)

        back_button.update(mouse_pos)
        back_button.draw(screen)

        header_font = get_font(28)
        row_font = get_font(26)
        headers = ["RANK", "NAME", "SCORE"]
        column_x_positions = [340, 520, 860]
        for header, x_pos in zip(headers, column_x_positions):
            screen.blit(header_font.render(header, True, (220, 220, 240)), (x_pos, 240))

        csv_path = tabs[active_tab_index][1]
        top_scores = get_top_scores(csv_path, top_n=5)

        y_pos = 290
        if not top_scores:
            screen.blit(get_font(28).render("No scores yet.", True, (180, 180, 200)), (520, y_pos))
        else:
            for row in top_scores:
                screen.blit(row_font.render(str(row["rank"]), True, (255, 255, 255)), (column_x_positions[0], y_pos))
                screen.blit(row_font.render(row["name"], True, (255, 255, 255)), (column_x_positions[1], y_pos))
                screen.blit(row_font.render(str(row["score"]), True, (255, 255, 255)), (column_x_positions[2], y_pos))
                y_pos += 50

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.MOUSEBUTTONDOWN:
                for tab_index, button in enumerate(tab_buttons):
                    if button.is_clicked(mouse_pos):
                        active_tab_index = tab_index
                if back_button.is_clicked(mouse_pos):
                    return

        pg.display.flip()
        clock.tick(60)


def how_to_play_screen():
    screen_width, screen_height = 1280, 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("How to Play")
    background = make_background(screen_width, screen_height, (18, 20, 35), (30, 18, 45))
    clock = pg.time.Clock()

    back_button = Button((40, 40, 160, 50), "BACK", get_font(32), (80, 80, 80), (110, 110, 110))

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_surface = get_font(70).render("HOW TO PLAY", True, (255, 215, 120))
        title_rect = title_surface.get_rect(center=(screen_width // 2, 70))
        screen.blit(title_surface, title_rect)

        back_button.update(mouse_pos)
        back_button.draw(screen)

        body_font = get_font(26)
        lines = [
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
        y_pos = 150
        for line in lines:
            screen.blit(body_font.render(line, True, (230, 230, 245)), (120, y_pos))
            y_pos += 34

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.MOUSEBUTTONDOWN:
                if back_button.is_clicked(mouse_pos):
                    return

        pg.display.flip()
        clock.tick(60)


def controls_screen():
    screen_width, screen_height = 1280, 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Controls")
    background = make_background(screen_width, screen_height, (18, 20, 35), (30, 18, 45))
    clock = pg.time.Clock()

    back_button = Button((40, 40, 160, 50), "BACK", get_font(32), (80, 80, 80), (110, 110, 110))

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_surface = get_font(70).render("CONTROLS", True, (255, 215, 120))
        title_rect = title_surface.get_rect(center=(screen_width // 2, 70))
        screen.blit(title_surface, title_rect)

        back_button.update(mouse_pos)
        back_button.draw(screen)

        body_font = get_font(30)
        y_pos = 170
        blocks = [
            (
                "SOLO MODE",
                [
                    "Move Left:   LEFT ARROW",
                    "Move Right:  RIGHT ARROW",
                    "Rotate:      UP ARROW",
                    "Soft Drop:   DOWN ARROW (hold)",
                    "Pause:       P",
                ],
            ),
            (
                "LOCAL MULTIPLAYER",
                [
                    "Player 1: W (rotate), A (left), S (down), D (right)",
                    "Player 2: I (rotate), J (left), K (down), L (right)",
                    "Player 3: Arrow Keys (Up rotate, Left/Right move, Down soft drop)",
                    "Pause (all match modes): P",
                ],
            ),
        ]

        for header, items in blocks:
            screen.blit(get_font(40).render(header, True, (220, 220, 240)), (120, y_pos))
            y_pos += 50
            for item in items:
                screen.blit(body_font.render(item, True, (230, 230, 245)), (150, y_pos))
                y_pos += 40
            y_pos += 25

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return
            if event.type == pg.MOUSEBUTTONDOWN:
                if back_button.is_clicked(mouse_pos):
                    return

        pg.display.flip()
        clock.tick(60)


def play_solo():
    result = practice_menu()
    if result is None:
        return
    speed, name = result

    app = App(solo_speed=speed, player_name=name)
    try:
        app.run()
    finally:
        if app.tetris and app.tetris.score > 0:
            append_solo_score(
                LEADERBOARD_SOLO_CSV,
                name=name,
                score=app.tetris.score,
                speed=app.tetris.manual_speed,
                level=app.tetris.level,
                lines=app.tetris.lines_cleared,
            )


def local_multiplayer_2p():
    from versus import MatchApp

    MatchApp(total_players=2, cpu_opponents=0, cpu_difficulty="medium", player_names=["Player 1", "Player 2"]).run()


def local_multiplayer_3p():
    from versus import MatchApp

    MatchApp(
        total_players=3,
        cpu_opponents=0,
        cpu_difficulty="medium",
        player_names=["Player 1", "Player 2", "Player 3"],
    ).run()


def main_menu():
    screen_width, screen_height = 1280, 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Tetris - Main Menu")

    background = make_background(screen_width, screen_height, (20, 20, 40), (40, 20, 60))

    button_width = 420
    button_height = 60
    start_y = 190
    spacing = 75
    centre_x = screen_width // 2

    buttons = {
        "practice": Button(
            (centre_x - button_width // 2, start_y, button_width, button_height),
            "PRACTICE (SOLO)",
            get_font(40),
            (50, 130, 160),
            (70, 160, 200),
        ),
        "local_2p": Button(
            (centre_x - button_width // 2, start_y + spacing, button_width, button_height),
            "LOCAL MULTIPLAYER (2P)",
            get_font(34),
            (140, 80, 150),
            (170, 110, 180),
        ),
        "local_3p": Button(
            (centre_x - button_width // 2, start_y + spacing * 2, button_width, button_height),
            "LOCAL MULTIPLAYER (3P)",
            get_font(34),
            (140, 80, 150),
            (170, 110, 180),
        ),
        "vs_cpu": Button(
            (centre_x - button_width // 2, start_y + spacing * 3, button_width, button_height),
            "VS CPU",
            get_font(40),
            (180, 60, 60),
            (210, 90, 90),
        ),
        "leaderboards": Button(
            (centre_x - button_width // 2, start_y + spacing * 4, button_width, button_height),
            "LEADERBOARDS",
            get_font(40),
            (70, 120, 80),
            (90, 150, 100),
        ),
        "howto": Button(
            (centre_x - button_width // 2, start_y + spacing * 5, button_width, button_height),
            "HOW TO PLAY",
            get_font(40),
            (60, 90, 130),
            (90, 130, 170),
        ),
        "controls": Button(
            (centre_x - button_width // 2, start_y + spacing * 6, button_width, button_height),
            "CONTROLS",
            get_font(40),
            (60, 90, 130),
            (90, 130, 170),
        ),
        "quit": Button(
            (centre_x - button_width // 2, start_y + spacing * 7, button_width, button_height),
            "QUIT",
            get_font(40),
            (80, 80, 80),
            (110, 110, 110),
        ),
    }

    clock = pg.time.Clock()

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(90)
        title_surface = title_font.render("TETRIS", True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(centre_x, 90))
        screen.blit(title_surface, title_rect)

        for button in buttons.values():
            button.update(mouse_pos)
            button.draw(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if buttons["practice"].is_clicked(mouse_pos):
                    play_solo()
                elif buttons["local_2p"].is_clicked(mouse_pos):
                    local_multiplayer_2p()
                elif buttons["local_3p"].is_clicked(mouse_pos):
                    local_multiplayer_3p()
                elif buttons["vs_cpu"].is_clicked(mouse_pos):
                    import versus_menu

                    versus_menu.versus_menu()
                elif buttons["leaderboards"].is_clicked(mouse_pos):
                    leaderboard_screen()
                elif buttons["howto"].is_clicked(mouse_pos):
                    how_to_play_screen()
                elif buttons["controls"].is_clicked(mouse_pos):
                    controls_screen()
                elif buttons["quit"].is_clicked(mouse_pos):
                    pg.quit()
                    sys.exit()

        pg.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    pg.init()
    main_menu()
