import pygame as pg
import sys
from button import Button
from settings import *
import versus


def get_font(font_size):
    return pg.font.Font("Tetris-NEA-main/Font/font.ttf", font_size)


SCREEN = pg.display.set_mode((1920, 1080))
BACKGROUND_IMAGE = pg.image.load("Tetris-NEA-main/Assets/Background.png")


def versus_menu():
    while True:
        SCREEN.blit(BACKGROUND_IMAGE, (0, 0))
        mouse_position = pg.mouse.get_pos()

        title_text = get_font(90).render("SELECT DIFFICULTY", True, "#b68f40")
        title_rect = title_text.get_rect(center=(960, 180))
        SCREEN.blit(title_text, title_rect)

        easy_button = Button(
            image=pg.image.load("Tetris-NEA-main/Assets/Play Rect.png"),
            pos=(960, 360),
            text_input="EASY",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White")

        medium_button = Button(
            image=pg.image.load("Tetris-NEA-main/Assets/Play Rect.png"),
            pos=(960, 480),
            text_input="MEDIUM",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White")

        hard_button = Button(
            image=pg.image.load("Tetris-NEA-main/Assets/Play Rect.png"),
            pos=(960, 600),
            text_input="HARD",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White")

        back_button = Button(
            image=None,
            pos=(960, 740),
            text_input="BACK",
            font=get_font(75),
            base_color="Black",
            hovering_color="Green")

        menu_buttons = [easy_button, medium_button, hard_button, back_button]
        for button in menu_buttons:
            button.changeColor(mouse_position)
            button.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if easy_button.checkForInput(mouse_position):
                    versus.VersusApp(difficulty="easy").run()

                if medium_button.checkForInput(mouse_position):
                    versus.VersusApp(difficulty="medium").run()

                if hard_button.checkForInput(mouse_position):
                    versus.VersusApp(difficulty="hard").run()

                if back_button.checkForInput(mouse_position):
                    return

        pg.display.update()
