"""Settings screen."""

from __future__ import annotations
from pathlib import Path
from typing import ClassVar

import pygame

from ..screen import Screen
from ...ui.button import Button
from ...ui.sprite import Sprite


class SettingsMenu(Screen):
    """Display the settings screen and its back button."""

    # TODO: Add controls for the shared music and sound effect volume.

    SETTINGS_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[3] / "asset_files" / "settings"

    SETTINGS_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "settings.png")

    BACK_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_unlit.png")
    BACK_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_lit.png")

    def __init__(self, app: App) -> None:
        """Create the back button and settings animation."""
        super().__init__(app)

        self.back_button = Button(
            position=(12, 12),
            unlit_img=self.BACK_BUTTON_UNLIT_IMG,
            lit_img=self.BACK_BUTTON_LIT_IMG,
            action=app.pop_screen
        )

        self.overlay_sprite = Sprite(
            self.SETTINGS_ASSET_DIR / "settings_overlay_sheet.png"
        )
        self.sprites = pygame.sprite.Group(self.overlay_sprite)

    def handle_event(self, event: pygame.event) -> None:
        """Handle input for the back button."""
        self.back_button.handle_event(event)

    def update(self, dt: float) -> None:
        """Update the settings animation."""
        self.overlay_sprite.update(dt)

    def draw(self, window: pygame.display) -> None:
        """Draw the settings background, back button, and animation."""
        window.blit(self.SETTINGS_IMG, (0, 0))
        self.back_button.draw(window)
        self.sprites.draw(window)
