from settings import *
from TetrisGame import Tetris, Text

import sys
import pathlib
import pygame as pg


# Font cache — stores loaded fonts so we don't reload them every frame
_font_cache = {}
_font_warning_shown = False

class App:
    """
    Solo Tetris app for practice or solo play (uses arrow keys).
    """
    def __init__(self):
        pg.display.set_caption("Tetris")
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        self.set_timer()
        self.images = self.load_sprites()

        self.tetris = Tetris(self)
        self.text = Text(self)

    def load_sprites(self):
        # Find all .png files in the sprite directory
        sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if item.is_file()]
        if not sprite_files:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")
            return []

        loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
        # Scale every sprite to match the tile size
        scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]
        return scaled_images

    def set_timer(self):
        # Two timer events: one for normal fall speed, one for when player holds down
        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1

        self.animation_trigger = False
        self.fast_animation_trigger = False

        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def update(self):
        self.tetris.update()
        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(color=BG_COLOUR)
        self.tetris.draw()
        self.text.draw()
        pg.display.flip()

    def check_events(self):
        # Reset triggers each frame — they get set to True by the timer events below
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                self.tetris.control(event.key)

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
    """
    Returns a font at the given size. Tries the custom font first,
    falls back to pygame's default. Caches every font it loads.
    """
    global _font_cache, _font_warning_shown

    # Return from cache if we already loaded this size
    if font_size in _font_cache:
        return _font_cache[font_size]

    try:
        font = pg.font.Font("Font/font.ttf", font_size)
        _font_cache[font_size] = font
        return font
    except FileNotFoundError:
        # Only print the warning once
        if not _font_warning_shown:
            print("Warning: Custom font 'Font/font.ttf' not found, using default pygame font")
            _font_warning_shown = True

        font = pg.font.Font(None, font_size)
        _font_cache[font_size] = font
        return font


def make_background(width, height, color1, color2):
    """Creates a vertical gradient surface blending from color1 at the top to color2 at the bottom."""
    surface = pg.Surface((width, height))
    for y in range(height):
        # blend_ratio goes 0.0 at top to 1.0 at bottom
        blend_ratio = y / height
        r = int(color1[0] * (1 - blend_ratio) + color2[0] * blend_ratio)
        g = int(color1[1] * (1 - blend_ratio) + color2[1] * blend_ratio)
        b = int(color1[2] * (1 - blend_ratio) + color2[2] * blend_ratio)
        pg.draw.line(surface, (r, g, b), (0, y), (width, y))
    return surface


def draw_button(surface, rect, text, font, is_hovering, base_color=(70, 130, 180), hover_color=(100, 160, 210)):
    # Shadow — drawn offset behind the button
    shadow_rect = rect.copy()
    shadow_rect.x += 5
    shadow_rect.y += 5
    pg.draw.rect(surface, (0, 0, 0, 128), shadow_rect, border_radius=15)

    # Pick colour based on whether the mouse is over the button
    color = hover_color if is_hovering else base_color

    pg.draw.rect(surface, color, rect, border_radius=15)
    # Thin white border for definition
    pg.draw.rect(surface, (255, 255, 255, 100), rect, width=2, border_radius=15)

    # Centre the label text inside the button
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)


class Button:
    """Clickable button with hover colour change."""
    def __init__(self, rect, text, font, base_color=(70, 130, 180), hover_color=(100, 160, 210)):
        self.rect = pg.Rect(rect)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.is_hovering = False

    def update(self, mouse_pos):
        # Check whether the mouse is inside this button's rectangle
        self.is_hovering = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        draw_button(surface, self.rect, self.text, self.font, self.is_hovering, self.base_color, self.hover_color)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# 

def play():
    """Launches solo practice mode."""
    App().run()

def local_multiplayer_2p():
    """Launches a 2-player local match with no CPU opponents."""
    from versus import MatchApp
    MatchApp(
        total_players=2,
        cpu_opponents=0,
        cpu_difficulty="medium",
        player_names=["Player 1", "Player 2"]).run()

def local_multiplayer_3p():
    """Launches a 3-player local match with no CPU opponents."""
    from versus import MatchApp
    MatchApp(
        total_players=3,
        cpu_opponents=0,
        cpu_difficulty="medium",
        player_names=["Player 1", "Player 2", "Player 3"]).run()


def main_menu():
    screen = pg.display.set_mode((1280, 720))
    pg.display.set_caption("Tetris - Main Menu")

    background = make_background(1280, 720, (20, 20, 40), (40, 20, 60))

    # Button layout constants
    button_width = 400
    button_height = 60
    start_y = 200
    spacing = 80
    center_x = 640

    # One Button per menu option, each with its own colour theme
    buttons = {
        'practice': Button((center_x - button_width//2, start_y, button_width, button_height),
                           "PRACTICE (SOLO)", get_font(40), (50, 130, 160), (70, 160, 200)),
        'local_2p': Button((center_x - button_width//2, start_y + spacing, button_width, button_height),
                           "LOCAL MULTIPLAYER (2P)", get_font(34), (140, 80, 150), (170, 110, 180)),
        'local_3p': Button((center_x - button_width//2, start_y + spacing*2, button_width, button_height),
                           "LOCAL MULTIPLAYER (3P)", get_font(34), (140, 80, 150), (170, 110, 180)),
        'vs_cpu':   Button((center_x - button_width//2, start_y + spacing*3, button_width, button_height),
                           "VS CPU", get_font(40), (180, 60, 60), (210, 90, 90)),
        'quit':     Button((center_x - button_width//2, start_y + spacing*4, button_width, button_height),
                           "QUIT", get_font(40), (80, 80, 80), (110, 110, 110))
    }
    clock = pg.time.Clock()

    while True:
        mouse_pos = pg.mouse.get_pos()
        screen.blit(background, (0, 0))

        # Title with a drop shadow behind it
        title_font = get_font(90)
        title_text = "TETRIS"
        title_shadow = title_font.render(title_text, True, (0, 0, 0))
        title_surface = title_font.render(title_text, True, (255, 215, 100))
        title_rect = title_surface.get_rect(center=(640, 100))
        screen.blit(title_shadow, (title_rect.x + 4, title_rect.y + 4))
        screen.blit(title_surface, title_rect)

        # Update hover state and draw every button
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

            # Route click to the correct game mode
            if event.type == pg.MOUSEBUTTONDOWN:
                if buttons['practice'].is_clicked(mouse_pos):
                    play()
                elif buttons['local_2p'].is_clicked(mouse_pos):
                    local_multiplayer_2p()
                elif buttons['local_3p'].is_clicked(mouse_pos):
                    local_multiplayer_3p()
                elif buttons['vs_cpu'].is_clicked(mouse_pos):
                    import versus_menu
                    versus_menu.versus_menu()
                elif buttons['quit'].is_clicked(mouse_pos):
                    pg.quit()
                    sys.exit()

        pg.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    pg.init()
    main_menu()