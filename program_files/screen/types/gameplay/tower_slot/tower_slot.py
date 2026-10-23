"""Handle tower slot positions and hover states."""

from pathlib import Path
from typing import ClassVar

import pygame


class TowerSlot:
    """Store a tower position and its placement and hover states."""

    TOWER_SLOT_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "tower"

    PAD_BLUE_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        TOWER_SLOT_ASSET_DIR / "pad_b.png")
    PAD_LBLUE_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        TOWER_SLOT_ASSET_DIR / "pad_lb.png")
    PAD_RED_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        TOWER_SLOT_ASSET_DIR / "pad_r.png")
    PAD_GREEN_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        TOWER_SLOT_ASSET_DIR / "pad_g.png")

    def __init__(self, position: tuple[int, int]) -> None:
        """Create an empty tower slot at the given position."""
        self.x_pos, self.y_pos = position
        self.rect = pygame.Rect(self.x_pos, self.y_pos, 24, 24)

        self.occupied = False
        self.selected = False
        self.hovering = False

    def draw(self, window: pygame.Surface) -> None:
        """Draw the slot image for its occupied and hover states."""
        if self.occupied and self.hovering:
            image = self.PAD_RED_IMG
        elif self.occupied:
            image = self.PAD_LBLUE_IMG
        elif self.hovering:
            image = self.PAD_GREEN_IMG
        else:
            image = self.PAD_BLUE_IMG

        window.blit(image, self.rect)
