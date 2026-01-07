import pygame as pg
import sys
import pathlib

from settings import *
from TetrisGame import Tetris, Text
from ai_tetris import NeuralNet, NeuralNetAgent, load_genes
from ai_config import AI_CONFIG


class AIApp:
    def __init__(self):
        pg.init()
        pg.display.set_caption('AI Tetris')
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()
        
        # Load sprites
        self.images = self.load_sprites()
        
        # Set up timers
        self.set_timer()
        
        # Create game
        self.tetris = Tetris(self, is_simulation=False)
        self.text = Text(self)

        # Initialize AI network
        try:
            genes = load_genes(AI_CONFIG["best_genome_file"])
            print(f"Loaded trained genes from {AI_CONFIG['best_genome_file']}")
            neural_net = NeuralNet(genes=genes)
        except Exception as e:
            print(f"Could not load {AI_CONFIG['best_genome_file']}: {e}")
            print("Using random neural net weights instead.")
            neural_net = NeuralNet()

        self.ai_agent = NeuralNetAgent(neural_net)
        self.ai_move_timer = 0
        self.ai_move_delay = AI_CONFIG["ai_move_delay"]

    def load_sprites(self):
        try:
            files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob('*.png')
                     if item.is_file()]
            if not files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_sprites()
            
            images = [pg.image.load(file).convert_alpha() for file in files]
            images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in images]
            print(f"Loaded {len(images)} sprites for AI mode")
            return images
        except Exception as e:
            print(f"Error loading sprites: {e}")
            return self.create_default_sprites()
    
    def create_default_sprites(self):
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 165, 0)
        ]
        sprites = []
        for color in colors:
            surf = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
            surf.fill(color)
            pg.draw.rect(surf, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surf)
        print("Created default colored sprites for AI mode")
        return sprites

    def set_timer(self):
        self.user_event = pg.USEREVENT + 0
        self.fast_user_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.user_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_user_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def ai_control(self):
        if self.tetris.game_over_flag:
            return
            
        self.ai_move_timer += 1
        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0
            
            # Get AI move
            move = self.ai_agent.choose_move(self.tetris)
            if move:
                print(f"AI chose move: rotation={move[0]}, target_x={move[1]}")
                self.tetris.apply_ai_move(move)

    def update(self):
        self.ai_control()
        self.tetris.update()
        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(color=BG_COLOUR)
        self.tetris.draw()
        self.text.draw()

        # Draw AI indicator
        font = pg.font.Font(None, 36)
        ai_text = font.render("AI PLAYING", True, (0, 255, 0))
        self.screen.blit(ai_text, (WIN_W * 0.6, WIN_H * 0.92))

        pg.display.flip()

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.user_event:
                self.animation_trigger = True
            elif event.type == self.fast_user_event:
                self.fast_animation_trigger = True
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                print(f"Current Score: {self.tetris.score}")
                print(f"Lines Cleared: {self.tetris.lines_cleared}")

    def run(self):
        print("AI Tetris started!")
        print("Press SPACE to see current score")
        print("Press ESC to quit")

        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    app = AIApp()
    app.run()