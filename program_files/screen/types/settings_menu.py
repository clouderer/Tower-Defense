from pathlib import Path 
from typing import ClassVar

import pygame

from ..screen import Screen
from ...ui.button import Button

class SettingsMenu(Screen):
    SETTINGS_ASSET_DIR: ClassVar[Path] = Path(__file__).resolve().parents[3] / "asset_files" / "settings"

    SETTINGS_IMG: ClassVar[pygame.Surface] = pygame.image.load(SETTINGS_ASSET_DIR / "settings.png")
    
    BACK_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(SETTINGS_ASSET_DIR / "back_unlit.png")
    BACK_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(SETTINGS_ASSET_DIR / "back_lit.png")

    def __init__(self, app): 
        super().__init__(app)

        self.back_button = Button(
            position = (12, 12),
            unlit_image = self.BACK_UNLIT_IMG, 
            lit_image = self.BACK_LIT_IMG, 
            action = app.get_main_menu
        )

    def handle_event(self, event):
        self.back_button.handle_event(event)

    def update(self, dt): 
        pass

    def draw(self, window):
        window.blit(self.SETTINGS_IMG, (0,0))
        self.back_button.draw(window)