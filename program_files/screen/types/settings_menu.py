"""Settings screen."""

from __future__ import annotations
from pathlib import Path
from typing import ClassVar

import pygame

from ..screen import Screen
from ...ui.button import Button
from ...ui.sprite import Sprite
from ...ui.volume_slider import VolumeSlider


class SettingsMenu(Screen):
    """Adjust music and tower sound volume from the settings screen."""

    SETTINGS_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[3] / "asset_files" / "settings"

    SETTINGS_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "settings.png")

    BACK_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_unlit.png")
    BACK_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        SETTINGS_ASSET_DIR / "back_lit.png")

    def __init__(self, app: App) -> None:
        """Create the back button, volume sliders, and animation."""
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
        self.music_slider = VolumeSlider(
            "MUSIC", (150, 162), app.volume.music_volume,
            self.set_music_volume,
        )
        self.sfx_slider = VolumeSlider(
            "SOUND EFFECTS", (150, 242), app.volume.sfx_volume,
            self.set_sfx_volume,
        )

    def set_music_volume(self, volume: float) -> None:
        """Change the song's loudness while it is playing."""
        self.app.volume.music_volume = volume
        pygame.mixer.music.set_volume(volume)

    def set_sfx_volume(self, volume: float) -> None:
        """Apply the new volume to all tower sounds."""
        self.app.volume.sfx_volume = volume
        self.app.audio.set_volume(volume)

    def handle_event(self, event: pygame.event) -> None:
        """Handle the back button and both volume sliders."""
        self.back_button.handle_event(event)
        self.music_slider.handle_event(event)
        self.sfx_slider.handle_event(event)

    def update(self, dt: float) -> None:
        """Update the settings animation."""
        self.overlay_sprite.update(dt)

    def draw(self, window: pygame.display) -> None:
        """Draw the settings background, animation, and controls."""
        window.blit(self.SETTINGS_IMG, (0, 0))
        self.sprites.draw(window)
        self.back_button.draw(window)
        self.music_slider.draw(window)
        self.sfx_slider.draw(window)
