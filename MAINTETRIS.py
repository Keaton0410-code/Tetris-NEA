from settings import *
from TetrisGame import Tetris, Text

import sys
import pathlib
import pygame as pg


# Global cache for font to avoid repeated warnings
_font_cache = {}
_font_warning_shown = False


class App:
    """
    Solo Tetris app.
    - ai_mode=False: human practice (arrow keys)
    - ai_mode=True: AI plays solo using provided ai_agent (easy/medium)
    """
    def __init__(self, ai_mode=False, ai_agent=None, ai_move_delay=20):
        pg.display.set_caption("Tetris")
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        self.ai_mode = ai_mode
        self.ai_agent = ai_agent
        self.ai_move_delay = ai_move_delay

        self.set_timer()
        self.images = self.load_sprites()

        self.tetris = Tetris(self)
        self.text = Text(self)

        # AI control state
        self.ai_move_timer = 0
        self.has_executed_current_move = False
        self.current_ai_move = None

    def load_sprites(self):
        sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if item.is_file()]
        if not sprite_files:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")
            return []

        loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
        scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]
        return scaled_images

    def set_timer(self):
        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1

        self.animation_trigger = False
        self.fast_animation_trigger = False

        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def ai_control(self):
        if not self.ai_agent:
            return

        self.ai_move_timer += 1
        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0

            if not self.has_executed_current_move:
                chosen_move = self.ai_agent.choose_move(self.tetris)
                if chosen_move:
                    self.current_ai_move = chosen_move
                    self.execute_ai_move(chosen_move)
                    self.has_executed_current_move = True

        # Allow a new move when a new tetromino is near the spawn area
        if self.tetris.tetromino.pos.y <= INIT_POS_OFFSET.y + 1:
            self.has_executed_current_move = False

    def execute_ai_move(self, move):
        if not move:
            return

        rotations, target_x_position = move

        for _ in range(rotations):
            self.tetris.tetromino.rotate()

        current_x_position = int(self.tetris.tetromino.blocks[0].pos.x)
        horizontal_shift = target_x_position - current_x_position

        if horizontal_shift > 0:
            for _ in range(horizontal_shift):
                self.tetris.tetromino.move("right")
        elif horizontal_shift < 0:
            for _ in range(abs(horizontal_shift)):
                self.tetris.tetromino.move("left")

        # Drop quickly once positioned
        self.tetris.speed_up = True

    def update(self):
        if self.ai_mode:
            self.ai_control()

        self.tetris.update()
        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(color=BG_COLOUR)
        self.tetris.draw()
        self.text.draw()

        if self.ai_mode:
            status_font = pg.font.Font(None, 36)
            ai_status_text = status_font.render("AI MODE", True, (0, 255, 0))
            self.screen.blit(ai_status_text, (WIN_W * 0.62, WIN_H * 0.92))

        pg.display.flip()

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()

            elif event.type == pg.KEYDOWN:
                if not self.ai_mode:
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


# ----------------------------
# Solo modes
# ----------------------------
def play():
    App(ai_mode=False).run()


def ai_play(difficulty="medium"):
    from ai_difficulty import get_ai_by_difficulty
    ai_agent = get_ai_by_difficulty(difficulty)
    App(ai_mode=True, ai_agent=ai_agent, ai_move_delay=20).run()


# ----------------------------
# Match modes (2–3 boards)
# ----------------------------
def local_multiplayer_2p():
    from versus import VersusApp
    VersusApp(
        total_players=2,
        cpu_opponents=0,
        cpu_difficulty="medium",
        player_names=["Player 1", "Player 2"]
    ).run()


def local_multiplayer_3p():
    from versus import VersusApp
    VersusApp(
        total_players=3,
        cpu_opponents=0,
        cpu_difficulty="medium",
        player_names=["Player 1", "Player 2", "Player 3"]
    ).run()


def vs_cpu_2p(cpu_difficulty="medium"):
    # 1 human vs 1 CPU (2 boards)
    from versus import VersusApp
    VersusApp(
        total_players=2,
        cpu_opponents=1,
        cpu_difficulty=cpu_difficulty,
        player_names=["Player 1", "CPU 1"]
    ).run()


def vs_cpu_3p(cpu_difficulty="medium"):
    # 1 human vs 2 CPU (3 boards)
    from versus import VersusApp
    VersusApp(
        total_players=3,
        cpu_opponents=2,
        cpu_difficulty=cpu_difficulty,
        player_names=["Player 1", "CPU 1", "CPU 2"]
    ).run()


def main_menu():
    from button import Button

    screen = pg.display.set_mode((1920, 1080))
    background_image = load_background()

    while True:
        if background_image:
            screen.blit(background_image, (0, 0))
        else:
            screen.fill((15, 20, 30))

        mouse_position = pg.mouse.get_pos()

        menu_title_text = get_font(100).render("MAIN MENU", True, "#b68f40")
        screen.blit(menu_title_text, menu_title_text.get_rect(center=(640, 100)))

        # Load button images with fallback (cached after first load)
        play_rect_img = load_button_image("Play Rect.png")
        quit_rect_img = load_button_image("Quit Rect.png")

        play_button = Button(
            image=play_rect_img,
            pos=(640, 200),
            text_input="PRACTICE (SOLO)",
            font=get_font(60),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        ai_easy_button = Button(
            image=play_rect_img,
            pos=(640, 310),
            text_input="AI PLAY (EASY)",
            font=get_font(60),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        ai_medium_button = Button(
            image=play_rect_img,
            pos=(640, 420),
            text_input="AI PLAY (MEDIUM)",
            font=get_font(60),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        local_2p_button = Button(
            image=play_rect_img,
            pos=(640, 530),
            text_input="LOCAL MULTIPLAYER (2P)",
            font=get_font(55),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        local_3p_button = Button(
            image=play_rect_img,
            pos=(640, 630),
            text_input="LOCAL MULTIPLAYER (3P)",
            font=get_font(55),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        vs_cpu_button = Button(
            image=play_rect_img,
            pos=(640, 730),
            text_input="VS CPU (1–2 CPU)",
            font=get_font(55),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        quit_button = Button(
            image=quit_rect_img,
            pos=(640, 840),
            text_input="QUIT",
            font=get_font(60),
            base_colour="#d7fcd4",
            hovering_colour="White"
        )

        buttons = [
            play_button,
            ai_easy_button,
            ai_medium_button,
            local_2p_button,
            local_3p_button,
            vs_cpu_button,
            quit_button
        ]

        for button in buttons:
            button.changeColor(mouse_position)
            button.update(screen)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if play_button.checkForInput(mouse_position):
                    play()

                if ai_easy_button.checkForInput(mouse_position):
                    ai_play(difficulty="easy")

                if ai_medium_button.checkForInput(mouse_position):
                    ai_play(difficulty="medium")

                if local_2p_button.checkForInput(mouse_position):
                    local_multiplayer_2p()

                if local_3p_button.checkForInput(mouse_position):
                    local_multiplayer_3p()

                if vs_cpu_button.checkForInput(mouse_position):
                    import versus_menu
                    versus_menu.versus_menu()

                if quit_button.checkForInput(mouse_position):
                    pg.quit()
                    sys.exit()

        pg.display.update()


if __name__ == "__main__":
    pg.init()
    main_menu()