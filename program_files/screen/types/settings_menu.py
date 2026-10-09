from pathlib import Path
from typing import ClassVar

import pygame

from ..screen import Screen
from ...ui.button import Button


class SettingsMenu(Screen):
    SETTINGS_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[3] / "asset_files" / "settings"

    SETTINGS_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "settings.png")

    BACK_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_unlit.png")
    BACK_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_lit.png")

    def __init__(self, app):
        '''
        Initialize the settings menu and its back button.
        '''
        super().__init__(app)

        self.back_button = Button(
            position=(12, 12),
            unlit_img=self.BACK_BUTTON_UNLIT_IMG,
            lit_img=self.BACK_BUTTON_LIT_IMG,
            action=app.pop_screen
        )

    def handle_event(self, event):
        '''
        Forward input to the back button.
        '''
        self.back_button.handle_event(event)

    def update(self, dt):
        '''
        Update the menu; it has no animated state to advance.
        '''
        pass

    def draw(self, window):
        '''
        Draw the settings background and back button.
        '''
        window.blit(self.SETTINGS_IMG, (0, 0))
        self.back_button.draw(window)
