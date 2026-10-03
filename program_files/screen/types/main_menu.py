from pathlib import Path

import pygame

from ..screen import Screen
from ...ui.button import Button


class MainMenu(Screen):
    MENU_ASSET_DIR = Path(__file__).resolve().parents[3] / "asset_files" / "menu"

    MENU_IMG = pygame.image.load(MENU_ASSET_DIR / "main_menu.png")
    PLAY_LIT_IMG = pygame.image.load(MENU_ASSET_DIR / "play_lit.png")
    PLAY_UNLIT_IMG = pygame.image.load(MENU_ASSET_DIR / "play_unlit.png")
    SETTING_UNLIT_IMG = pygame.image.load(MENU_ASSET_DIR / "setting_unlit.png")
    SETTING_LIT_IMG = pygame.image.load(MENU_ASSET_DIR / "setting_lit.png")

    def __init__(self, app):
        super().__init__(app)

        self.play_button = Button(
            position = (207, 218),
            unlit_img=self.PLAY_UNLIT_IMG,
            lit_img=self.PLAY_LIT_IMG,
            action=self.app.get_map_selection,
        )

        self.settings_button = Button(
            position=(207, 270),
            unlit_img=self.SETTING_UNLIT_IMG,
            lit_img=self.SETTING_LIT_IMG,
            action=self.app.get_settings,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.app.get_map_selection()
            elif event.key == pygame.K_s:
                self.app.get_settings()

        self.play_button.handle_event(event)
        self.settings_button.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, window):
        window.blit(self.MENU_IMG, (0, 0))
        self.play_button.draw(window)
        self.settings_button.draw(window)

