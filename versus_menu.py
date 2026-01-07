import pygame as pg
import sys
from button import Button
from settings import *
import versus


def get_font(size):
    return pg.font.Font("Tetris NEA/Font/font.ttf", size)


SCREEN = pg.display.set_mode((1920, 1080))
BG = pg.image.load("Tetris NEA/Assets/Background.png")


def versus_menu():
    while True:
        SCREEN.blit(BG, (0, 0))
        MENU_MOUSE_POS = pg.mouse.get_pos()

        TITLE = get_font(90).render("SELECT DIFFICULTY", True, "#b68f40")
        TITLE_RECT = TITLE.get_rect(center=(960, 180))
        SCREEN.blit(TITLE, TITLE_RECT)

        EASY_BTN = Button(
            image=pg.image.load("Tetris NEA/Assets/Play Rect.png"),
            pos=(960, 360),
            text_input="EASY",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        MEDIUM_BTN = Button(
            image=pg.image.load("Tetris NEA/Assets/Play Rect.png"),
            pos=(960, 480),
            text_input="MEDIUM",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        HARD_BTN = Button(
            image=pg.image.load("Tetris NEA/Assets/Play Rect.png"),
            pos=(960, 600),
            text_input="HARD",
            font=get_font(75),
            base_color="#d7fcd4",
            hovering_color="White"
        )

        BACK_BTN = Button(
            image=None,
            pos=(960, 740),
            text_input="BACK",
            font=get_font(75),
            base_color="Black",
            hovering_color="Green"
        )

        for button in [EASY_BTN, MEDIUM_BTN, HARD_BTN, BACK_BTN]:
            button.changeColor(MENU_MOUSE_POS)
            button.update(SCREEN)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.MOUSEBUTTONDOWN:
                if EASY_BTN.checkForInput(MENU_MOUSE_POS):
                    versus.VersusApp(difficulty="easy").run()

                if MEDIUM_BTN.checkForInput(MENU_MOUSE_POS):
                    versus.VersusApp(difficulty="medium").run()

                if HARD_BTN.checkForInput(MENU_MOUSE_POS):
                    versus.VersusApp(difficulty="hard").run()

                if BACK_BTN.checkForInput(MENU_MOUSE_POS):
                    return

        pg.display.update()