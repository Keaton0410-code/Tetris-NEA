import pygame as pg
import pathlib

from settings import *
from TetrisGame import Tetris
from ai_difficulty import get_ai_by_difficulty


class VersusApp:
    def __init__(self, difficulty="medium"):
        pg.init()
        pg.display.set_caption("Tetris – Versus")

        #Window setup
        window_width_pixels = (FIELD_W * 2 + 6) * TILE_SIZE
        window_height_pixels = FIELD_H * TILE_SIZE + 120
        self.screen = pg.display.set_mode((window_width_pixels, window_height_pixels))
        self.clock = pg.time.Clock()

        #Load sprites
        self.images = self.load_sprites()

        #Timer setup
        self.normal_tick_event = pg.USEREVENT + 0
        self.fast_tick_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.normal_tick_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_tick_event, FAST_ANIMAMATION_TIME_INTERVAL)

        #Create games
        self.human_game = Tetris(self, offset_tiles=vec(0, 0), is_simulation=False)
        self.ai_game = Tetris(self, offset_tiles=vec(FIELD_W + 4, 0), is_simulation=False)

        #AI setup
        self.ai_agent = get_ai_by_difficulty(difficulty)
        self.ai_move_timer = 0
        self.ai_move_delay = 20
        self.difficulty_label = difficulty.upper()

    def load_sprites(self):
        try:
            sprite_files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") 
                            if item.is_file()]
            
            if not sprite_files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_sprites()

            loaded_images = [pg.image.load(file).convert_alpha() for file in sprite_files]
            scaled_images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in loaded_images]
            print(f"Loaded {len(scaled_images)} sprites for versus mode")
            return scaled_images

        except Exception as error:
            print(f"Error loading sprites: {error}")
            return self.create_default_sprites()

    def create_default_sprites(self):
        colours = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
            (255, 165, 0)]
        
        sprites = []
        for colour in colours:
            surface = pg.Surface((TILE_SIZE, TILE_SIZE), pg.SRCALPHA)
            surface.fill(colour)
            pg.draw.rect(surface, (255, 255, 255), (0, 0, TILE_SIZE, TILE_SIZE), 2)
            sprites.append(surface)
        print("Created default coloured sprites for versus mode")
        return sprites

    def ai_control(self):
        if self.ai_game.game_over_flag:
            return

        self.ai_move_timer += 1
        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0

            chosen_move = self.ai_agent.choose_move(self.ai_game)
            if chosen_move:
                self.ai_game.apply_ai_move(chosen_move)

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                raise SystemExit

            if event.type == pg.KEYDOWN and not self.human_game.game_over_flag:
                self.human_game.control(event.key)

            if event.type == self.normal_tick_event:
                self.animation_trigger = True

            if event.type == self.fast_tick_event:
                self.fast_animation_trigger = True

    def update(self):
        self.ai_control()
        self.human_game.update()
        self.ai_game.update()
        self.clock.tick(FPS)

    def draw(self):
        self.screen.fill((30, 40, 60))
        self.human_game.draw()
        self.ai_game.draw()
        self.draw_ui()
        pg.display.flip()

    def draw_ui(self):
        heading_font = pg.font.Font(None, 36)
        body_font = pg.font.Font(None, 28)

        #Human player
        human_label = "HUMAN"
        if self.human_game.game_over_flag:
            human_label = "HUMAN - GAME OVER"

        human_text = heading_font.render(human_label, True, (255, 220, 100))
        human_centre_x = (FIELD_W * TILE_SIZE) // 2
        self.screen.blit(human_text, (human_centre_x - human_text.get_width() // 2, 10))

        human_score_text = body_font.render(f"Score: {self.human_game.score}", True, (255, 255, 200))
        self.screen.blit(human_score_text, (10, FIELD_H * TILE_SIZE + 30))

        #AI player
        ai_panel_offset_x = (FIELD_W + 4) * TILE_SIZE
        ai_label = f"AI ({self.difficulty_label})"
        if self.ai_game.game_over_flag:
            ai_label = f"AI ({self.difficulty_label}) - GAME OVER"

        ai_text = heading_font.render(ai_label, True, (100, 255, 100))
        ai_centre_x = ai_panel_offset_x + (FIELD_W * TILE_SIZE // 2)
        self.screen.blit(ai_text, (ai_centre_x - ai_text.get_width() // 2, 10))

        ai_score_text = body_font.render(f"Score: {self.ai_game.score}", True, (200, 255, 200))
        self.screen.blit(ai_score_text, (ai_panel_offset_x + 10, FIELD_H * TILE_SIZE + 30))

        # Game over message
        if self.human_game.game_over_flag and self.ai_game.game_over_flag:
            result_font = pg.font.Font(None, 48)

            if self.human_game.score > self.ai_game.score:
                message_text = "HUMAN WINS!"
                message_colour = (255, 255, 0)
            elif self.ai_game.score > self.human_game.score:
                message_text = "AI WINS!"
                message_colour = (255, 100, 100)
            else:
                message_text = "DRAW!"
                message_colour = (200, 200, 200)

            result_text = result_font.render(message_text, True, message_colour)
            self.screen.blit(result_text,(self.screen.get_width() // 2 - result_text.get_width() // 2,FIELD_H * TILE_SIZE + 80))

            exit_text = body_font.render("Press ESC to exit", True, (255, 255, 255))
            self.screen.blit(
                exit_text, (self.screen.get_width() // 2 - exit_text.get_width() // 2,
                    FIELD_H * TILE_SIZE + 140))

    def run(self):
        print(f"Versus Mode: Human vs AI ({self.difficulty_label})")
        print("Controls: Arrow keys for Human player")
        print("Press ESC to exit")

        while True:
            try:
                self.check_events()
                self.update()
                self.draw()
            except SystemExit:
                break
