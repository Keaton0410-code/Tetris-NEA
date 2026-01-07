import pygame as pg
import pathlib
from settings import *
from TetrisGame import Tetris
from ai_difficulty import get_ai_by_difficulty


class VersusApp:
    def __init__(self, difficulty="medium"):
        pg.init()
        pg.display.set_caption("Tetris – Versus")
        
        # Window setup
        window_width = (FIELD_W * 2 + 6) * TILE_SIZE
        window_height = FIELD_H * TILE_SIZE + 120
        self.screen = pg.display.set_mode((window_width, window_height))
        self.clock = pg.time.Clock()
        
        # Load sprites
        self.images = self.load_sprites()
        
        # Timer setup
        self.user_event = pg.USEREVENT + 0
        self.fast_user_event = pg.USEREVENT + 1
        self.animation_trigger = False
        self.fast_animation_trigger = False
        pg.time.set_timer(self.user_event, ANIMATION_TIME_INTERVAL)
        pg.time.set_timer(self.fast_user_event, FAST_ANIMAMATION_TIME_INTERVAL)
        
        # Create games
        self.human_game = Tetris(self, offset_tiles=vec(0, 0), is_simulation=False)
        self.ai_game = Tetris(self, offset_tiles=vec(FIELD_W + 4, 0), is_simulation=False)
        
        # AI setup
        self.ai = get_ai_by_difficulty(difficulty)
        self.ai_move_timer = 0
        self.ai_move_delay = 20
        self.difficulty = difficulty.upper()

    def load_sprites(self):
        try:
            files = [item for item in pathlib.Path(SPRITE_DIRECTORY_PATH).rglob("*.png") if item.is_file()]
            if not files:
                print(f"No sprites found at {SPRITE_DIRECTORY_PATH}")
                return self.create_default_sprites()
            
            images = [pg.image.load(file).convert_alpha() for file in files]
            images = [pg.transform.scale(image, (TILE_SIZE, TILE_SIZE)) for image in images]
            print(f"Loaded {len(images)} sprites for versus mode")
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
        print("Created default colored sprites for versus mode")
        return sprites

    def ai_control(self):
        if self.ai_game.game_over_flag:
            return
            
        self.ai_move_timer += 1
        if self.ai_move_timer >= self.ai_move_delay:
            self.ai_move_timer = 0
            
            # Get AI move
            move = self.ai.choose_move(self.ai_game)
            if move:
                # Apply move to AI game
                self.ai_game.apply_ai_move(move)

    def check_events(self):
        self.animation_trigger = False
        self.fast_animation_trigger = False
        
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                raise SystemExit
            
            if event.type == pg.KEYDOWN and not self.human_game.game_over_flag:
                self.human_game.control(event.key)
            
            if event.type == self.user_event:
                self.animation_trigger = True
            
            if event.type == self.fast_user_event:
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
        font = pg.font.Font(None, 36)
        small_font = pg.font.Font(None, 28)
        
        # Human player
        human_label = "HUMAN"
        if self.human_game.game_over_flag:
            human_label = "HUMAN - GAME OVER"
        
        human_text = font.render(human_label, True, (255, 220, 100))
        human_x = (FIELD_W * TILE_SIZE) // 2
        self.screen.blit(human_text, (human_x - human_text.get_width()//2, 10))
        
        human_score = small_font.render(f"Score: {self.human_game.score}", True, (255, 255, 200))
        self.screen.blit(human_score, (10, FIELD_H * TILE_SIZE + 30))
        
        # AI player
        ai_offset = (FIELD_W + 4) * TILE_SIZE
        ai_label = f"AI ({self.difficulty})"
        if self.ai_game.game_over_flag:
            ai_label = f"AI ({self.difficulty}) - GAME OVER"
        
        ai_text = font.render(ai_label, True, (100, 255, 100))
        ai_x = ai_offset + (FIELD_W * TILE_SIZE // 2)
        self.screen.blit(ai_text, (ai_x - ai_text.get_width()//2, 10))
        
        ai_score = small_font.render(f"Score: {self.ai_game.score}", True, (200, 255, 200))
        self.screen.blit(ai_score, (ai_offset + 10, FIELD_H * TILE_SIZE + 30))
        
        # Game over message
        if self.human_game.game_over_flag and self.ai_game.game_over_flag:
            result_font = pg.font.Font(None, 48)
            if self.human_game.score > self.ai_game.score:
                message = "HUMAN WINS!"
                color = (255, 255, 0)
            elif self.ai_game.score > self.human_game.score:
                message = f"AI WINS!"
                color = (255, 100, 100)
            else:
                message = "DRAW!"
                color = (200, 200, 200)
            
            result_text = result_font.render(message, True, color)
            self.screen.blit(result_text, 
                           (self.screen.get_width()//2 - result_text.get_width()//2,
                            FIELD_H * TILE_SIZE + 80))
            
            esc_text = small_font.render("Press ESC to exit", True, (255, 255, 255))
            self.screen.blit(esc_text, 
                           (self.screen.get_width()//2 - esc_text.get_width()//2,
                            FIELD_H * TILE_SIZE + 140))

    def run(self):
        print(f"Versus Mode: Human vs AI ({self.difficulty})")
        print("Controls: Arrow keys for Human player")
        print("Press ESC to exit")
        
        while True:
            try:
                self.check_events()
                self.update()
                self.draw()
            except SystemExit:
                break