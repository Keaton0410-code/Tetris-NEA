from settings import *

import pygame as pg
import sys
import versus


_font_cache = {}
_font_warning_shown = False


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
            print("Warning: Custom font not found, using default")
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


def draw_button(surface, rect, text, font, is_hovering, is_selected=False):
    if is_selected:
        button_colour = (60, 180, 80)
    elif is_hovering:
        button_colour = (90, 130, 170)
    else:
        button_colour = (60, 90, 130)

    pg.draw.rect(surface, button_colour, rect, border_radius=10)

    border_colour = (200, 255, 200) if is_selected else ((180, 180, 200) if is_hovering else (100, 120, 140))
    border_width = 3 if is_selected else 2
    pg.draw.rect(surface, border_colour, rect, width=border_width, border_radius=10)

    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)


class Button:
    def __init__(self, rect, text, font):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.is_hovering = False
        self.is_selected = False

    def update(self, mouse_pos):
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.is_hovering, self.is_selected)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


class TextInput:
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
        bg_colour = (50, 100, 150) if self.is_active else (40, 60, 90)
        pg.draw.rect(surface, bg_colour, self.rect, border_radius=8)

        border_colour = (100, 200, 255) if self.is_active else (80, 100, 120)
        border_width = 3 if self.is_active else 2
        pg.draw.rect(surface, border_colour, self.rect, width=border_width, border_radius=8)

        label_font = get_font(20)
        label_surface = label_font.render(self.label, True, (180, 180, 200))
        surface.blit(label_surface, (self.rect.left, self.rect.top - 25))

        value_font = get_font(26)
        shown_text = self.text if self.text else "(click to type)"
        text_colour = (255, 255, 255) if self.text else (120, 120, 140)
        value_surface = value_font.render(shown_text, True, text_colour)
        surface.blit(value_surface, (self.rect.left + 12, self.rect.centery - 13))


def draw_header(surface, text, x, y, font):
    text_surface = font.render(text, True, (220, 220, 240))
    text_rect = text_surface.get_rect(centerx=x, top=y)
    surface.blit(text_surface, text_rect)

    line_y = text_rect.bottom + 4
    pg.draw.line(surface, (100, 120, 150), (x - 100, line_y), (x + 100, line_y), 2)
    return text_rect.bottom + 12


def versus_menu():
    pg.init()
    screen_width = 1280
    screen_height = 720
    screen = pg.display.set_mode((screen_width, screen_height))
    pg.display.set_caption("Match Setup")

    background = make_background(screen_width, screen_height, (20, 25, 40), (35, 20, 50))

    total_players = 2
    cpu_opponents = 1
    cpu_difficulty = "medium"

    centre_x = screen_width // 2
    left_column_x = 320
    right_column_x = 960
    button_width = 200
    button_height = 55
    button_spacing = 70

    board2_button = Button((left_column_x - button_width // 2, 120, button_width, button_height), "2 BOARDS", get_font(32))
    board3_button = Button((right_column_x - button_width // 2, 120, button_width, button_height), "3 BOARDS", get_font(32))

    cpu0_button = Button((left_column_x - button_width // 2, 240, button_width, button_height), "0 CPU", get_font(30))
    cpu1_button = Button((left_column_x - button_width // 2, 240 + button_spacing, button_width, button_height), "1 CPU", get_font(30))
    cpu2_button = Button((left_column_x - button_width // 2, 240 + button_spacing * 2, button_width, button_height), "2 CPU", get_font(30))

    easy_button = Button((right_column_x - button_width // 2, 240, button_width, button_height), "EASY", get_font(30))
    medium_button = Button((right_column_x - button_width // 2, 240 + button_spacing, button_width, button_height), "MEDIUM", get_font(30))

    player1_box = TextInput((centre_x, 480), label="PLAYER 1 NAME")
    player2_box = TextInput((centre_x, 545), label="PLAYER 2 NAME")
    player3_box = TextInput((centre_x, 610), label="PLAYER 3 NAME")

    start_button = Button((centre_x - 210, 665, 200, 50), "START MATCH", get_font(32))
    back_button = Button((centre_x + 10, 665, 200, 50), "BACK", get_font(32))

    all_buttons = [
        board2_button,
        board3_button,
        cpu0_button,
        cpu1_button,
        cpu2_button,
        easy_button,
        medium_button,
        start_button,
        back_button,
    ]

    clock = pg.time.Clock()

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        title_font = get_font(60)
        title_surface = title_font.render("MATCH SETUP", True, (255, 215, 120))
        title_rect = title_surface.get_rect(center=(centre_x, 45))
        screen.blit(title_surface, title_rect)

        header_font = get_font(24)
        draw_header(screen, "NUMBER OF BOARDS", centre_x, 85, header_font)
        draw_header(screen, "CPU OPPONENTS", left_column_x, 200, header_font)
        if cpu_opponents > 0:
            draw_header(screen, "CPU DIFFICULTY", right_column_x, 200, header_font)
        draw_header(screen, "PLAYER NAMES", centre_x, 430, header_font)

        board2_button.is_selected = (total_players == 2)
        board3_button.is_selected = (total_players == 3)
        cpu0_button.is_selected = (cpu_opponents == 0)
        cpu1_button.is_selected = (cpu_opponents == 1)
        cpu2_button.is_selected = (cpu_opponents == 2)
        easy_button.is_selected = (cpu_difficulty == "easy")
        medium_button.is_selected = (cpu_difficulty == "medium")

        max_cpu_allowed = total_players - 1
        if cpu_opponents > max_cpu_allowed:
            cpu_opponents = max_cpu_allowed
        if cpu_opponents < 0:
            cpu_opponents = 0

        human_players = total_players - cpu_opponents

        for button in all_buttons:
            button.update(mouse_pos)
            button.draw(screen)

        if human_players >= 1:
            player1_box.draw(screen)
        if human_players >= 2:
            player2_box.draw(screen)
        if human_players >= 3:
            player3_box.draw(screen)

        info_font = get_font(18)
        info_text = "Controls: P1=WASD | P2=IJKL | P3=Arrows(Up,Down,Left,Right)"
        info_surface = info_font.render(info_text, True, (120, 130, 150))
        info_rect = info_surface.get_rect(center=(centre_x, 645))
        screen.blit(info_surface, info_rect)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            player1_box.handle_event(event)
            player2_box.handle_event(event)
            player3_box.handle_event(event)

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return

            if event.type == pg.MOUSEBUTTONDOWN:
                if board2_button.is_clicked(mouse_pos):
                    total_players = 2
                elif board3_button.is_clicked(mouse_pos):
                    total_players = 3
                elif cpu0_button.is_clicked(mouse_pos):
                    cpu_opponents = 0
                elif cpu1_button.is_clicked(mouse_pos):
                    cpu_opponents = 1
                elif cpu2_button.is_clicked(mouse_pos):
                    cpu_opponents = 2
                elif easy_button.is_clicked(mouse_pos) and cpu_opponents > 0:
                    cpu_difficulty = "easy"
                elif medium_button.is_clicked(mouse_pos) and cpu_opponents > 0:
                    cpu_difficulty = "medium"
                elif start_button.is_clicked(mouse_pos):
                    p1 = player1_box.text.strip() or "Player 1"
                    p2 = player2_box.text.strip() or "Player 2"
                    p3 = player3_box.text.strip() or "Player 3"

                    names = []
                    if human_players >= 1:
                        names.append(p1)
                    if human_players >= 2:
                        names.append(p2)
                    if human_players >= 3:
                        names.append(p3)
                    for cpu_index in range(cpu_opponents):
                        names.append(f"CPU {cpu_index + 1}")

                    versus.MatchApp(
                        total_players=total_players,
                        cpu_opponents=cpu_opponents,
                        cpu_difficulty=cpu_difficulty,
                        player_names=names,
                    ).run()
                elif back_button.is_clicked(mouse_pos):
                    return

        pg.display.flip()
        clock.tick(60)
