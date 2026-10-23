"""Define the BitBlaster tower."""

from pathlib import Path
from typing import ClassVar


import pygame

from .tower import Tower, TowerLevel


class BitBlaster(Tower):
    """Attack quickly at short range."""
    NAME: ClassVar[str] = "BIT_BLASTER"
    COST: ClassVar[int] = 120
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(60, 2, 180, 100),
        TowerLevel(70, 3, 150, 400),
        TowerLevel(80, 5, 120, None),
    )

    BITBLASTER_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "bitblaster"
    RANGE_SHEETS: ClassVar[tuple[Path, ...]] = (
        BITBLASTER_ASSET_DIR / "bitblaster_level_1_60px_sheet.png",
        BITBLASTER_ASSET_DIR / "bitblaster_level_2_70px_sheet.png",
        BITBLASTER_ASSET_DIR / "bitblaster_level_3_80px_sheet.png",
    )

    def __init__(self, tower_slot: "TowerSlot") -> None:
        """Load the BitBlaster's images and place it on its slot."""
        super().__init__(tower_slot)

        self.image = pygame.image.load(
            self.BITBLASTER_ASSET_DIR / "bitblaster.png")

        self.rect = self.get_rect()

        self.overlay_img = pygame.image.load(
            self.BITBLASTER_ASSET_DIR / "bitblaster_overlay.png")

        self.sidebar = pygame.image.load(
            self.BITBLASTER_ASSET_DIR / "bitblaster_sidebar.png")
