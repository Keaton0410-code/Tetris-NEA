from settings import *

import pygame as pg
import sys
import versus

_font_cache = {}
_font_warning_shown = False

def get_font(font_size):
    """Returns a cached font at the given size falling back to pygame default if the custom font is missing."""
    global _font_cache, _font_warning_shown
    if font_size in _font_cache:
        return _font_cache[font_size]

    try:
        font = pg.font.Font("Font/font.ttf", font_size)
        _font_cache[font_size] = font
        return font
    except FileNotFoundError:
        # Only warn once
        if not _font_warning_shown:
            print("Warning: Custom font not found, using default")
            _font_warning_shown = True
        font = pg.font.Font(None, font_size)
        _font_cache[font_size] = font
        return font

def make_background(width, height, colour1, colour2):
    """Builds a vertical gradient surface from colour1 (top) to colour2 (bottom)."""
    surface = pg.Surface((width, height))
    for y in range(height):
        # 0.0 at the top, 1.0 at the bottom
        blend_ratio = y / height
        r = int(colour1[0] * (1 - blend_ratio) + colour2[0] * blend_ratio)
        g = int(colour1[1] * (1 - blend_ratio) + colour2[1] * blend_ratio)
        b = int(colour1[2] * (1 - blend_ratio) + colour2[2] * blend_ratio)
        pg.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface

def draw_button(surface, rect, text, font, is_hovering, is_selected=False):
    """Draws a button with shadow a colour that reacts to hover/selection, border, and centred text."""
    # Drop shadow
    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    pg.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=10)

    #Green when active selection, lighter blue on hover, darker blue otherwise
    if is_selected:
        base_color = (60, 180, 80)
    elif is_hovering:
        base_color = (90, 130, 170)
    else:
        base_color = (60, 90, 130)
    pg.draw.rect(surface, base_color, rect, border_radius=10)

    #Border brightens and thickens for selected/hovered state
    border_color = (200, 255, 200) if is_selected else ((180, 180, 200) if is_hovering else (100, 120, 140))
    border_width = 3 if is_selected else 2
    pg.draw.rect(surface, border_color, rect, width=border_width, border_radius=10)

    # Centre the label
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

class Button:
    def __init__(self, rect, text, font):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.is_hovering = False
        self.is_selected = False  # externally to highlight the current choice

    def update(self, mouse_pos):
        # True when the cursor is inside the button rectangle
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.is_hovering, self.is_selected)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class TextInput:
    """A single line text box the player can click and type into."""
    def __init__(self, centre_pos, width=350, height=50, label="PLAYER"):
        self.rect = pg.Rect(0, 0, width, height)
        self.rect.center = centre_pos
        self.is_active = False  # True while the box has keyboard focus
        self.text = ""
        self.label = label

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            self.is_active = self.rect.collidepoint(event.pos)

        if event.type == pg.KEYDOWN and self.is_active:
            if event.key == pg.K_BACKSPACE:
                # Delete the last character
                self.text = self.text[:-1]
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_TAB):
                # Confirm and lose focus
                self.is_active = False
            else:
                # Only accept printable chars, max 15 long
                if len(self.text) < 15 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface):
        shadow_rect = self.rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        pg.draw.rect(surface, (0, 0, 0, 80), shadow_rect, border_radius=8)

        # Background brightens when focused
        bg_color = (50, 100, 150) if self.is_active else (40, 60, 90)
        pg.draw.rect(surface, bg_color, self.rect, border_radius=8)

        # Border brightens and thickens when focused
        border_color = (100, 200, 255) if self.is_active else (80, 100, 120)
        border_width = 3 if self.is_active else 2
        pg.draw.rect(surface, border_color, self.rect, width=border_width, border_radius=8)

        # Label drawn above the box
        label_font = get_font(20)
        label_surface = label_font.render(self.label, True, (180, 180, 200))
        surface.blit(label_surface, (self.rect.left, self.rect.top - 25))

        # Show placeholder when empty, otherwise the typed text
        value_font = get_font(26)
        shown_text = self.text if self.text else "(click to type)"
        text_color = (255, 255, 255) if self.text else (120, 120, 140)
        value_surface = value_font.render(shown_text, True, text_color)
        surface.blit(value_surface, (self.rect.left + 12, self.rect.centery - 13))


def draw_header(surface, text, x, y, font):
    text_surface = font.render(text, True, (220, 220, 240))
    text_rect = text_surface.get_rect(centerx=x, top=y)
    surface.blit(text_surface, text_rect)

    # Underline
    line_y = text_rect.bottom + 4
    pg.draw.line(surface, (100, 120, 150), (x - 100, line_y), (x + 100, line_y), 2)
    return text_rect.bottom + 12

def versus_menu():
    pg.init()
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("Match Setup")

    #render gradient so it isn't rebuilt every frame
    background = make_background(SCREEN_WIDTH, SCREEN_HEIGHT, (20, 25, 40), (35, 20, 50))

    #Current state 
    total_players = 2
    cpu_opponents = 1
    cpu_difficulty = "medium"

    #Layout constants 
    CENTER_X = SCREEN_WIDTH // 2
    LEFT_COL_X = 320
    RIGHT_COL_X = 960
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 55
    BUTTON_SPACING = 70

    #Board buttons
    board2_btn = Button((LEFT_COL_X - BUTTON_WIDTH//2, 120, BUTTON_WIDTH, BUTTON_HEIGHT), "2 BOARDS", get_font(32))
    board3_btn = Button((RIGHT_COL_X - BUTTON_WIDTH//2, 120, BUTTON_WIDTH, BUTTON_HEIGHT),"3 BOARDS", get_font(32))

    cpu0_btn = Button((LEFT_COL_X - BUTTON_WIDTH//2, 240, BUTTON_WIDTH, BUTTON_HEIGHT),"0 CPU", get_font(30))
    cpu1_btn = Button((LEFT_COL_X - BUTTON_WIDTH//2, 240 + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT),"1 CPU", get_font(30))
    cpu2_btn = Button((LEFT_COL_X - BUTTON_WIDTH//2, 240 + BUTTON_SPACING*2, BUTTON_WIDTH, BUTTON_HEIGHT),"2 CPU", get_font(30))

    easy_btn   = Button((RIGHT_COL_X - BUTTON_WIDTH//2, 240, BUTTON_WIDTH, BUTTON_HEIGHT),"EASY", get_font(30))
    medium_btn = Button((RIGHT_COL_X - BUTTON_WIDTH//2, 240 + BUTTON_SPACING, BUTTON_WIDTH, BUTTON_HEIGHT),"MEDIUM", get_font(30))

    player1_box = TextInput((CENTER_X, 480), label="PLAYER 1 NAME")
    player2_box = TextInput((CENTER_X, 545), label="PLAYER 2 NAME")
    player3_box = TextInput((CENTER_X, 610), label="PLAYER 3 NAME")

    start_btn = Button((CENTER_X - 210, 665, 200, 50), "START MATCH", get_font(32))
    back_btn  = Button((CENTER_X + 10,  665, 200, 50), "BACK",        get_font(32))

    all_buttons = [board2_btn, board3_btn, cpu0_btn, cpu1_btn, cpu2_btn,easy_btn, medium_btn, start_btn, back_btn]

    clock = pg.time.Clock()

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        #Title with drop shadow
        title_font = get_font(60)
        title_text = "MATCH SETUP"
        title_shadow = title_font.render(title_text, True, (0, 0, 0))
        title_surface = title_font.render(title_text, True, (255, 215, 120))
        title_rect = title_surface.get_rect(center=(CENTER_X, 45))
        screen.blit(title_shadow,  (title_rect.x + 3, title_rect.y + 3))
        screen.blit(title_surface, title_rect)

        # Section headers
        header_font = get_font(24)
        draw_header(screen, "NUMBER OF BOARDS", CENTER_X,    85,  header_font)
        draw_header(screen, "CPU OPPONENTS",    LEFT_COL_X,  200, header_font)

        # Only show difficulty header when there is at least one CPU
        if cpu_opponents > 0:
            draw_header(screen, "CPU DIFFICULTY", RIGHT_COL_X, 200, header_font)
        draw_header(screen, "PLAYER NAMES", CENTER_X, 430, header_font)

        board2_btn.is_selected= (total_players == 2)
        board3_btn.is_selected= (total_players == 3)
        cpu0_btn.is_selected = (cpu_opponents == 0)
        cpu1_btn.is_selected = (cpu_opponents == 1)
        cpu2_btn.is_selected = (cpu_opponents == 2)
        easy_btn.is_selected = (cpu_difficulty == "easy")
        medium_btn.is_selected= (cpu_difficulty == "medium")

        max_cpu_allowed = total_players - 1
        if cpu_opponents > max_cpu_allowed:
            cpu_opponents = max_cpu_allowed
        if cpu_opponents < 0:
            cpu_opponents = 0

        human_players = total_players - cpu_opponents

        #Draw all buttons 
        for button in all_buttons:
            button.update(mouse_pos)
            button.draw(screen)

        #draw difficulty buttons on top only when visible
        if cpu_opponents > 0:
            easy_btn.draw(screen)
            medium_btn.draw(screen)

        #Only show name inputs for human slots
        if human_players >= 1:
            player1_box.draw(screen)
        if human_players >= 2:
            player2_box.draw(screen)
        if human_players >= 3:
            player3_box.draw(screen)

        #Controls hint
        info_font = get_font(18)
        info_text = "Controls: P1=WASD | P2=IJKL | P3=Arrows(Up,Down,Left,Right)"
        info_surface = info_font.render(info_text, True, (120, 130, 150))
        info_rect = info_surface.get_rect(center=(CENTER_X, 645))
        screen.blit(info_surface, info_rect)

        #Event handling
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
                # Board count
                if board2_btn.is_clicked(mouse_pos):
                    total_players = 2
                elif board3_btn.is_clicked(mouse_pos):
                    total_players = 3
                # CPU count
                elif cpu0_btn.is_clicked(mouse_pos):
                    cpu_opponents = 0
                elif cpu1_btn.is_clicked(mouse_pos):
                    cpu_opponents = 1
                elif cpu2_btn.is_clicked(mouse_pos):
                    cpu_opponents = 2
                elif easy_btn.is_clicked(mouse_pos) and cpu_opponents > 0:
                    cpu_difficulty = "easy"
                elif medium_btn.is_clicked(mouse_pos) and cpu_opponents > 0:
                    cpu_difficulty = "medium"
                elif start_btn.is_clicked(mouse_pos):
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
                        player_names=names).run()
                    
                elif back_btn.is_clicked(mouse_pos):
                    return

        pg.display.flip()
        clock.tick(60)