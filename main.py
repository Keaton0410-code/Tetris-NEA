from settings import *
from TetrisGame import Tetris, Text
import sys
import pathlib
import pygame as pg


class App:
    def __init__(self):
        pg.init()
        pg.display.set_caption('Tetris')
        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()
        
        # Load sprites
        self.images = self.load_sprites()
        
        # Set up timers
        self.set_timer()
        
        # Create game
        self.tetris = Tetris(self)
        self.text = Text(self)

    def load_sprites(self):
        try:
            files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob('*.png') if item.is_file()]
            if not files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_sprites()
            
            images = [pg.image.load(file).convert_alpha() for file in files]
            images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in images]
            print(f"Loaded {len(images)} sprites")
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
        print("Created default colored sprites")
        return sprites

    def set_timer(self):
        self.user_event = pg.USEREVENT + 0
        self.fast_user_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.user_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_user_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def update(self):
        self.tetris.update()
        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill(color=BG_COLOUR)
        self.tetris.draw()
        self.text.draw()
        pg.display.flip()

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False
        
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            
            elif event.type == pg.KEYDOWN:
                self.tetris.control(pressed_key=event.key)
            
            elif event.type == self.user_event:
                self.animation_trigger = True
            
            elif event.type == self.fast_user_event:
                self.fast_animation_trigger = True

    def run(self):
        print("Tetris started! Use arrow keys to play.")
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    app = App()
    app.run()