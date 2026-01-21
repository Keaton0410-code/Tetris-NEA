from settings import *
from TetrisGame import Tetris, Text
import sys
import pathlib
import pygame as pg
import versus_menu


class App:
    def __init__(self, ai_mode=False):
        pg.display.set_caption('Tetris')
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        self.set_timer()
        self.images = self.load_sprites()

        self.tetris = Tetris(self)
        self.text = Text(self)

        self.ai_mode = ai_mode
        if self.ai_mode:
            from ai_tetris import NeuralNet, NeuralNetAgent, load_genes
            from ai_config import AI_CONFIG

            try:
                genome_genes = load_genes(AI_CONFIG["best_genome_file"])
                neural_network = NeuralNet(genes=genome_genes)
                print("Loaded trained AI genome successfully!")
            except:
                print("No trained genome found. Using a random neural network.")
                neural_network = NeuralNet()

            self.ai_agent = NeuralNetAgent(neural_network)

            self.ai_move_timer = 0
            self.ai_move_delay = AI_CONFIG["ai_move_delay"]

            self.current_ai_move = None
            self.has_executed_current_move = False

    def load_sprites(self):
        sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob('*.png')if item.is_file()]
        if not sprite_files:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")

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
        self.ai_move_timer += 1

        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0
            if not self.has_executed_current_move:
                chosen_move = self.ai_agent.choose_move(self.tetris)
                if chosen_move:
                    self.current_ai_move = chosen_move
                    self.execute_ai_move(chosen_move)
                    self.has_executed_current_move = True

        #Allows a new move to be chosen when the next tetromino spawns near the top
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
                elif event.key == pg.K_SPACE:
                    print("Score:", self.tetris.score)
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
    return pg.font.Font("Tetris NEA/Font/font.ttf", font_size)

SCREEN = pg.display.set_mode((1920, 1080))
BACKGROUND_IMAGE = pg.image.load("Tetris NEA/Assets/Background.png")

def play():
    App(ai_mode=False).run()

def ai_play():
    App(ai_mode=True).run()

def main_menu():
    while True:
        SCREEN.blit(BACKGROUND_IMAGE, (0, 0))
        mouse_position = pg.mouse.get_pos()

        menu_title_text = get_font(100).render("MAIN MENU", True, "#b68f40")
        SCREEN.blit(menu_title_text, menu_title_text.get_rect(center=(640, 100)))

        play_button = Button(
            pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 200),
            "PLAY",
            get_font(75),
            "#d7fcd4", "White")

        ai_play_button = Button(
            pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 320),
            "AI PLAY",
            get_font(75),
            "#d7fcd4", "White")

        versus_button = Button(
            pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 680),
            "AI VS HUMAN",
            get_font(75),
            "#d7fcd4", "White")

        options_button = Button(
            pg.image.load("Tetris NEA/Assets/Options Rect.png"), (640, 440),
            "OPTIONS",
            get_font(75),
            "#d7fcd4", "White")

        quit_button = Button(
            pg.image.load("Tetris NEA/Assets/Quit Rect.png"),(640, 560),
            "QUIT",
            get_font(75),
            "#d7fcd4", "White")

        buttons = [play_button, ai_play_button, options_button, quit_button, versus_button]

        for button in buttons:
            button.changeColor(mouse_position)
            button.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if play_button.checkForInput(mouse_position):
                    play()
                if ai_play_button.checkForInput(mouse_position):
                    ai_play()
                if versus_button.checkForInput(mouse_position):
                    versus_menu.versus_menu()
                if options_button.checkForInput(mouse_position):
                    pass
                if quit_button.checkForInput(mouse_position):
                    pg.quit()
                    sys.exit()
        pg.display.update()

if __name__ == "__main__":
    from button import Button
    pg.init()
    main_menu()
