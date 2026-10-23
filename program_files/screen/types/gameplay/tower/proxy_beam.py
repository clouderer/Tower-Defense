"""Define the Proxy Beam tower."""

from pathlib import Path
from typing import ClassVar


import pygame

from .tower import Tower, TowerLevel


class ProxyBeam(Tower):
    """Attack one enemy at long range."""

    NAME: ClassVar[str] = "PROXY_BEAM"
    COST: ClassVar[int] = 250
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(120, 22, 2000, 200),
        TowerLevel(135, 33, 1650, 500),
        TowerLevel(150, 49, 1300, None),
    )

    PROXYBEAM_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "proxybeam"
    RANGE_SHEETS: ClassVar[tuple[Path, ...]] = (
        PROXYBEAM_ASSET_DIR / "proxy_level_1_120px_sheet.png",
        PROXYBEAM_ASSET_DIR / "proxy_level_2_135px_sheet.png",
        PROXYBEAM_ASSET_DIR / "proxy_level_3_150px_sheet.png",
    )

    def __init__(self, tower_slot: "TowerSlot") -> None:
        """Load the Proxy Beam's images and place it on its slot."""
        super().__init__(tower_slot)

        self.image = pygame.image.load(
            self.PROXYBEAM_ASSET_DIR / "proxybeam.png")
        center_x, center_y = tower_slot.rect.center
        self.offset_center = (center_x, center_y - 5)
        self.rect = self.get_rect(center=self.offset_center)

        self.overlay_img = pygame.image.load(
            self.PROXYBEAM_ASSET_DIR / "proxybeam_overlay.png")

        self.sidebar = pygame.image.load(
            self.PROXYBEAM_ASSET_DIR / "proxy_sidebar.png"
        )
