"""Main menu screen"""

from __future__ import annotations
from pathlib import Path
from typing import ClassVar

import pygame

from ..screen import Screen
from ...ui.button import Button
from ...ui.sprite import Sprite


class MainMenu(Screen):
    """Display the play and settings buttons."""

    MENU_ASSET_DIR: ClassVar[Path] = Path(__file__).resolve(
    ).parents[3] / "asset_files" / "menu"

    MENU_IMG: ClassVar[pygame.image] =  pygame.image.load(MENU_ASSET_DIR / "main_menu.png")
    PLAY_LIT_IMG: ClassVar[pygame.image] =  pygame.image.load(MENU_ASSET_DIR / "play_lit.png")
    PLAY_UNLIT_IMG: ClassVar[pygame.image] = pygame.image.load(MENU_ASSET_DIR / "play_unlit.png")
    SETTING_UNLIT_IMG: ClassVar[pygame.image] = pygame.image.load(MENU_ASSET_DIR / "setting_unlit.png")
    SETTING_LIT_IMG: ClassVar[pygame.image] = pygame.image.load(MENU_ASSET_DIR / "setting_lit.png")

    def __init__(self, app: App) -> None:
        """Create the main menu buttons and animation."""
        super().__init__(app)

        self.play_button = Button(
            position=(207, 218),
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

        self.overlay_sprite = Sprite(
            self.MENU_ASSET_DIR / "main_menu_overlay_sheet.png"
        )
        self.sprites = pygame.sprite.Group(self.overlay_sprite)

    def handle_event(self, event: pygame.event) -> None:
        """Handle the button input."""
        self.play_button.handle_event(event)
        self.settings_button.handle_event(event)

    def update(self, dt: float) -> None:
        """Update the menu animation."""
        self.overlay_sprite.update(dt)

    def draw(self, window: pygame.display) -> None:
        """Draw the menu background, buttons, and animation."""
        window.blit(self.MENU_IMG, (0, 0))
        self.play_button.draw(window)
        self.settings_button.draw(window)
        self.sprites.draw(window)
