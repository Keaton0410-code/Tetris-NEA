import pygame as pg
import sys
from button import Button
from settings import *
import versus


# Global cache for font to avoid repeated warnings
_font_cache = {}
_font_warning_shown = False


def get_font(font_size):
    """
    Load custom font with fallback to pygame default font.
    Uses caching to avoid repeated file access and warnings.
    """
    global _font_cache, _font_warning_shown
    
    # Check cache first
    if font_size in _font_cache:
        return _font_cache[font_size]
    
    # Try to load custom font
    try:
        font = pg.font.Font("Font/font.ttf", font_size)
        _font_cache[font_size] = font
        return font
    except FileNotFoundError:
        # Only show warning once
        if not _font_warning_shown:
            print("Warning: Custom font 'Font/font.ttf' not found, using default pygame font")
            _font_warning_shown = True
        
        # Use default font
        font = pg.font.Font(None, font_size)
        _font_cache[font_size] = font
        return font


def load_background():
    """
    Load background image with error handling.
    """
    paths_to_try = [
        "Tetris-NEA-main/Assets/Background.png",
        "Assets/Background.png",
        "Background.png"
    ]
    
    for path in paths_to_try:
        try:
            return pg.image.load(path)
        except:
            continue
    
    return None


def load_button_image(filename):
    """
    Load button image with error handling.
    Returns None if image not found (button will use text-only mode).
    """
    paths_to_try = [
        f"Tetris-NEA-main/Assets/{filename}",
        f"Assets/{filename}",
        filename
    ]
    
    for path in paths_to_try:
        try:
            return pg.image.load(path)
        except:
            continue
    
    return None



#text input helper

class NameInputBox:
    def __init__(self, centre_pos, width=520, height=70, label="PLAYER"):
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
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.is_active = False
            else:
                if len(self.text) < 12 and event.unicode.isprintable():
                    self.text += event.unicode

    def draw(self, surface):
        box_colour = (70, 200, 120) if self.is_active else (220, 220, 220)
        pg.draw.rect(surface, box_colour, self.rect, 3)

        label_font = get_font(30)
        value_font = get_font(40)

        label_surface = label_font.render(self.label, True, "White")
        surface.blit(label_surface, (self.rect.left, self.rect.top - 40))

        shown_text = self.text if self.text else "(click to type)"
        value_surface = value_font.render(shown_text, True, "White")
        surface.blit(value_surface, (self.rect.left + 12, self.rect.top + 12))


def versus_menu():
    # Make sure pygame is initialised (safe even if already initialised)
    pg.init()

    # Create / reuse the same window for this menu screen
    screen = pg.display.set_mode((1920, 1080))
    background_image = load_background()

    # Defaults
    total_players = 2         # 2 or 3 boards
    cpu_opponents = 1         # 0..2 (but clamped by total_players)
    cpu_difficulty = "medium" # "easy" / "medium"

    # Name boxes (shown depending on number of humans)
    player1_box = NameInputBox((960, 360), label="PLAYER 1 NAME")
    player2_box = NameInputBox((960, 470), label="PLAYER 2 NAME")
    player3_box = NameInputBox((960, 580), label="PLAYER 3 NAME")

    # Load button image once (cached)
    play_rect_img = load_button_image("Play Rect.png")

    while True:
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((15, 20, 30))

        mouse_position = pg.mouse.get_pos()

        # Title
        title_text = get_font(80).render("MATCH SETUP", True, "#b68f40")
        screen.blit(title_text, title_text.get_rect(center=(960, 120)))

        # Buttons: total players 
        two_players_button = Button(
            image=play_rect_img,
            pos=(480, 220),
            text_input="2 BOARDS",
            font=get_font(45),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        three_players_button = Button(
            image=play_rect_img,
            pos=(960, 220),
            text_input="3 BOARDS",
            font=get_font(45),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Buttons: CPU count 
        cpu0_button = Button(
            image=play_rect_img,
            pos=(480, 290),
            text_input="0 CPU",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        cpu1_button = Button(
            image=play_rect_img,
            pos=(960, 290),
            text_input="1 CPU",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        cpu2_button = Button(
            image=play_rect_img,
            pos=(1440, 290),
            text_input="2 CPU",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        # Buttons: CPU difficulty 
        easy_cpu_button = Button(
            image=play_rect_img,
            pos=(480, 760),
            text_input="CPU: EASY",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        medium_cpu_button = Button(
            image=play_rect_img,
            pos=(960, 760),
            text_input="CPU: MEDIUM",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        start_button = Button(
            image=play_rect_img,
            pos=(1440, 760),
            text_input="START MATCH",
            font=get_font(40),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        back_button = Button(
            image=None,
            pos=(960, 880),
            text_input="BACK",
            font=get_font(60),
            base_color="Black",
            hovering_color="Green"
        )

        all_buttons = [
            two_players_button, three_players_button,
            cpu0_button, cpu1_button, cpu2_button,
            easy_cpu_button, medium_cpu_button,
            start_button, back_button
        ]

        for button in all_buttons:
            button.changeColor(mouse_position)
            button.update(screen)

        # Clamp CPU vs players (always keep at least 1 human)
        # maximum CPU is total_players - 1 (because at least 1 human must exist)
        max_cpu_allowed = total_players - 1
        if cpu_opponents > max_cpu_allowed:
            cpu_opponents = max_cpu_allowed
        if cpu_opponents < 0:
            cpu_opponents = 0

        human_players = total_players - cpu_opponents  # 1..3

        # Info display
        info_font = get_font(32)
        info_text = f"Boards: {total_players}   |   CPU: {cpu_opponents}   |   CPU difficulty: {cpu_difficulty.upper()}"
        screen.blit(info_font.render(info_text, True, "White"), (280, 320))

        # Draw name boxes for humans
        if human_players >= 1:
            player1_box.draw(screen)
        if human_players >= 2:
            player2_box.draw(screen)
        if human_players >= 3:
            player3_box.draw(screen)

        # Events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            # Name input
            player1_box.handle_event(event)
            player2_box.handle_event(event)
            player3_box.handle_event(event)

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                return

            if event.type == pg.MOUSEBUTTONDOWN:
                if two_players_button.checkForInput(mouse_position):
                    total_players = 2  # CPU clamping happens automatically above

                if three_players_button.checkForInput(mouse_position):
                    total_players = 3

                if cpu0_button.checkForInput(mouse_position):
                    cpu_opponents = 0

                if cpu1_button.checkForInput(mouse_position):
                    cpu_opponents = 1

                if cpu2_button.checkForInput(mouse_position):
                    cpu_opponents = 2  # clamped if total_players == 2

                if easy_cpu_button.checkForInput(mouse_position):
                    cpu_difficulty = "easy"

                if medium_cpu_button.checkForInput(mouse_position):
                    cpu_difficulty = "medium"

                if start_button.checkForInput(mouse_position):
                    # Clean names
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

                    # Add CPU names
                    for cpu_index in range(cpu_opponents):
                        names.append(f"CPU {cpu_index + 1}")

                    versus.VersusApp(
                        total_players=total_players,
                        cpu_opponents=cpu_opponents,
                        cpu_difficulty=cpu_difficulty,
                        player_names=names
                    ).run()

                if back_button.checkForInput(mouse_position):
                    return

        pg.display.update()