"""Define the Proxy Beam tower."""

from pathlib import Path
from typing import ClassVar


import pygame

from ..beam import Beam
from .tower import Tower, TowerLevel


class ProxyBeam(Tower):
    """Attack one enemy at long range."""

    NAME: ClassVar[str] = "PROXY_BEAM"
    COST: ClassVar[int] = 250
    BEAM_DURATION: ClassVar[float] = 0.78
    IMPACT_COLUMNS: ClassVar[int] = 8
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(120, 22, 2000, 200),
        TowerLevel(135, 33, 1650, 500),
        TowerLevel(150, 49, 1300, None),
    )

    PROXYBEAM_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "proxybeam"
    EMITTER_SHEET: ClassVar[Path] = (
        PROXYBEAM_ASSET_DIR / "proxy_emitter_sheet.png"
    )
    IMPACT_SHEET: ClassVar[Path] = (
        PROXYBEAM_ASSET_DIR / "proxy_impact_sheet.png"
    )
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
        self.beam: Beam | None = None

    def attack(self, current_time: int) -> int:
        """Connect a beam and damage its target on each attack."""
        target = self.target
        previous_attack_time = self.last_attack_time
        reward = super().attack(current_time)
        if self.last_attack_time != previous_attack_time:
            self.beam = Beam(
                self.rect.center, target, self.range,
                self.EMITTER_SHEET, self.IMPACT_SHEET,
                duration=self.BEAM_DURATION,
            )
        return reward

    def update(self, dt: float) -> None:
        """Update the tower and follow its target during the burst."""
        super().update(dt)
        if self.beam is not None:
            self.beam.update(dt)
            if self.beam.finished:
                self.beam = None

    def draw_attack_effect(self, window: pygame.Surface) -> None:
        """Draw the beam above enemies and towers."""
        if self.beam is not None:
            self.beam.draw(window)

    def stop_attack_effect(self) -> None:
        """Remove the beam when the tower is sold or gameplay ends."""
        self.beam = None
