from pathlib import Path

import pygame

from ..screen import Screen
from ...ui.text_object import TextObject

class MainMenu(Screen):
    def __init__(self, app):
        super().__init__(app)

        self.main_menu = pygame.image.load(Path("asset_files/menu/main_menu.png"))

        # [TO DO]: Replace these with a button object that can be clicked
        self.start_text = TextObject(
            text = "Press [Enter] to start",
            color = "White",
            position = (300, 237),
            font_size = 16,
        )

        self.settings_text = TextObject(
            text = "Press [S] for settings",
            color = "White",
            position = (300, 289),
            font_size = 16,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.app.get_gameplay()
            elif event.key == pygame.K_s:
                self.app.get_settings()

    def update(self, dt):
        pass

    def draw(self, window):
        window.blit(self.main_menu, (0, 0))

        self.start_text.draw(window)
        self.settings_text.draw(window)
    
