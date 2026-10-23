"""Define the Firewall Pulse tower."""

from pathlib import Path
from typing import ClassVar


import pygame

from .tower import Tower, TowerLevel


class FirewallPulse(Tower):
    """Attack one enemy within the tower's range."""

    NAME: ClassVar[str] = "FIREWALL_PULSE"
    COST: ClassVar[int] = 100
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(75, 6, 650, 80),
        TowerLevel(85, 9, 525, 350),
        TowerLevel(100, 13, 400, None),
    )

    FIREWALL_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "firewallpulse"
    RANGE_SHEETS: ClassVar[tuple[Path, ...]] = (
        FIREWALL_ASSET_DIR / "firewall_level_1_75px_sheet.png",
        FIREWALL_ASSET_DIR / "firewall_level_2_85px_sheet.png",
        FIREWALL_ASSET_DIR / "firewall_level_3_100px_sheet.png",
    )

    def __init__(self, tower_slot: "TowerSlot") -> None:
        """Load the Firewall Pulse's images and place it on its slot."""
        super().__init__(tower_slot)

        self.image = pygame.image.load(
            self.FIREWALL_ASSET_DIR / "firewall.png")
        self.rect = self.get_rect()

        self.overlay_img = pygame.image.load(
            self.FIREWALL_ASSET_DIR / "firewall_overlay.png")

        self.sidebar = pygame.image.load(
            self.FIREWALL_ASSET_DIR / "firewall_sidebar.png"
        )
