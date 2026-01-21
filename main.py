import sys
import pathlib
import pygame as pg

from settings import *
from TetrisGame import Tetris, Text

class App:
#Main application class for Tetris game application

    def __init__(self) -> None:
        pg.init()
        pg.display.set_caption("Tetris")

        self.screen = pg.display.set_mode(WIN_RES)
        self.clock = pg.time.Clock()

        #Load sprites used to render tetromino tiles
        self.tile_sprites = self.load_tile_sprites()

        #Configure repeating timer events for gravity/animation
        self.configure_timers()

        #Create game systems
        self.tetris = Tetris(self)
        self.text = Text(self)

        self.animation_trigger = False
        self.fast_animation_trigger = False

    def load_tile_sprites(self) -> list[pg.Surface]:
        #Load tile sprites from SPRITE_DIRECTORY_PATH. 
        try:
            sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png")if item.is_file()]

            if not sprite_files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_tile_sprites()

            loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
            scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]

            print(f"Loaded {len(scaled_images)} sprites")
            return scaled_images

        except Exception as exc:
            print(f"Error loading sprites: {exc}")
            return self.create_default_tile_sprites()

    def create_default_tile_sprites(self) -> list[pg.Surface]:
        #Use simple coloured sprites if no images found
        colours = [
            (255, 0, 0),     # red
            (0, 255, 0),     # green
            (0, 0, 255),     # blue
            (255, 255, 0),   # yellow
            (255, 0, 255),   # magenta
            (0, 255, 255),   # cyan
            (255, 165, 0),]  # orange

        sprites: list[pg.Surface] = []
        for colour in colours:
            surface = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
            surface.fill(colour)
            pg.draw.rect(surface, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surface)

        print("Using default coloured sprites")
        return sprites

    def configure_timers(self) -> None:
        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1

        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

    def update(self) -> None:
        self.tetris.update()
        self.clock.tick(FPS)

    def draw(self) -> None:
        self.screen.fill(BG_COLOUR)
        self.tetris.draw()
        self.text.draw()
        pg.display.flip()

    def handle_events(self) -> None:
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    pg.quit()
                    sys.exit()
                self.tetris.control(pressed_key=event.key)
            elif event.type == self.normal_tick_event:
                self.animation_trigger = True
            elif event.type == self.fast_tick_event:
                self.fast_animation_trigger = True

    def run(self) -> None:
        print("Tetris started.")
        print("Use arrow keys to play.")
        while True:
            self.handle_events()
            self.update()
            self.draw()


if __name__ == "__main__":
    App().run()
