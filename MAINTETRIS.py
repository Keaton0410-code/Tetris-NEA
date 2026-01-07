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
                genes = load_genes(AI_CONFIG["best_genome_file"])
                nn = NeuralNet(genes=genes)
                print("Loaded trained AI genome successfully!")
            except:
                print("No trained genome found. Using random neural net.")
                nn = NeuralNet()

            self.ai_agent = NeuralNetAgent(nn)
            self.ai_move_timer = 0
            self.ai_move_delay = AI_CONFIG["ai_move_delay"]
            self.current_ai_move = None
            self.move_executed = False

    def load_sprites(self):
        files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob('*.png') if item.is_file()]
        if not files:
            print(f"Warning: No .png files found in {SPRITE_DIRECTORY_PATH}")
        images = [pg.image.load(file).convert_alpha() for file in files]
        return [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in images]

    def set_timer(self):
        self.user_event = pg.USEREVENT + 0
        self.fast_user_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.user_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_user_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def ai_control(self):
        self.ai_move_timer += 1

        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0

            if not self.move_executed:
                move = self.ai_agent.choose_move(self.tetris)
                if move:
                    self.current_ai_move = move
                    self.execute_ai_move(move)
                    self.move_executed = True

        if self.tetris.tetromino.pos.y <= INIT_POS_OFFSET.y + 1:
            self.move_executed = False

    def execute_ai_move(self, move):
        if not move:
            return

        rot, target_x = move

        for _ in range(rot):
            self.tetris.tetromino.rotate()

        cx = int(self.tetris.tetromino.blocks[0].pos.x)
        shift = target_x - cx

        if shift > 0:
            for _ in range(shift):
                self.tetris.tetromino.move("right")
        elif shift < 0:
            for _ in range(abs(shift)):
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
            font = pg.font.Font(None, 36)
            ai_text = font.render("AI MODE", True, (0, 255, 0))
            self.screen.blit(ai_text, (WIN_W * 0.62, WIN_H * 0.92))

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

            elif event.type == self.user_event:
                self.animation_trigger = True

            elif event.type == self.fast_user_event:
                self.fast_animation_trigger = True

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


def get_font(size):
    return pg.font.Font("Tetris NEA/Font/font.ttf", size)


SCREEN = pg.display.set_mode((1920, 1080))
BG = pg.image.load("Tetris NEA/Assets/Background.png")


def play():
    App(ai_mode=False).run()


def ai_play():
    App(ai_mode=True).run()


def main_menu():
    while True:
        SCREEN.blit(BG, (0, 0))
        mouse = pg.mouse.get_pos()

        MENU_TEXT = get_font(100).render("MAIN MENU", True, "#b68f40")
        SCREEN.blit(MENU_TEXT, MENU_TEXT.get_rect(center=(640, 100)))

        PLAY_BTN = Button(pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 200),
                          "PLAY", get_font(75), "#d7fcd4", "White")

        AI_BTN = Button(pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 320),
                        "AI PLAY", get_font(75), "#d7fcd4", "White")

        VERSUS_BTN = Button(pg.image.load("Tetris NEA/Assets/Play Rect.png"), (640, 680),
                            "AI VS HUMAN", get_font(75), "#d7fcd4", "White")

        OPT_BTN = Button(pg.image.load("Tetris NEA/Assets/Options Rect.png"), (640, 440),
                         "OPTIONS", get_font(75), "#d7fcd4", "White")

        QUIT_BTN = Button(pg.image.load("Tetris NEA/Assets/Quit Rect.png"), (640, 560),
                          "QUIT", get_font(75), "#d7fcd4", "White")

        buttons = [PLAY_BTN, AI_BTN, OPT_BTN, QUIT_BTN, VERSUS_BTN]

        for b in buttons:
            b.changeColor(mouse)
            b.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if PLAY_BTN.checkForInput(mouse):
                    play()
                if AI_BTN.checkForInput(mouse):
                    ai_play()
                if VERSUS_BTN.checkForInput(mouse):
                    versus_menu.versus_menu()
                if OPT_BTN.checkForInput(mouse):
                    pass
                if QUIT_BTN.checkForInput(mouse):
                    pg.quit()
                    sys.exit()

        pg.display.update()


if __name__ == "__main__":
    from button import Button
    pg.init()
    main_menu()