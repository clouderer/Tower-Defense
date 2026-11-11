"""Animate the CPU at the exit and show how much health it has left."""

from pathlib import Path
from typing import ClassVar

import pygame

from ....ui.sprite import Sprite


class CPU(Sprite):
    """Flash red on a hit and turn grey as the player's health drops."""

    ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[4] / "asset_files" / "cpu"
    )
    RED_IMAGE: ClassVar[pygame.Surface] = pygame.image.load(
        ASSET_DIR / "cpu_red.png"
    )
    GREY_IMAGE: ClassVar[pygame.Surface] = pygame.image.load(
        ASSET_DIR / "cpu_grey.png"
    )
    FLASH_DURATION: ClassVar[float] = 0.25

    def __init__(self, position: tuple[int, int]) -> None:
        """Center the CPU animation on the path's last point."""
        super().__init__(
            self.ASSET_DIR / "cpu.png", x_cnt=1, y_cnt=1,
        )
        self.rect.center = position
        self.flash_remaining = 0.0
        self.grey_image = self.GREY_IMAGE.copy()
        self.grey_image.set_alpha(0)

    def flash(self) -> None:
        """Start a short red flash when an enemy gets through."""
        self.flash_remaining = self.FLASH_DURATION

    def update(self, dt: float) -> None:
        """Loop the CPU colors and count down its damage flash."""
        super().update(dt)
        self.flash_remaining = max(0.0, self.flash_remaining - dt)

    def draw(
        self,
        window: pygame.Surface,
        health: float,
        max_health: float,
    ) -> None:
        """Draw the CPU, its red flash, and the grey health overlay."""
        window.blit(self.image, self.rect)
        if self.flash_remaining > 0:
            window.blit(self.RED_IMAGE, self.rect)
        remaining_health = max(0.0, min(1.0, health / max_health))
        self.grey_image.set_alpha(round(255 * (1 - remaining_health)))
        window.blit(self.grey_image, self.rect)
