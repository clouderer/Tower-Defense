from typing import ClassVar
from pathlib import Path

import pygame

from .tower import Tower


class ProxyBeam(Tower):
    NAME: ClassVar[str] = "PROXY_BEAM"
    COST: ClassVar[int] = 250

    PROXYBEAM_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "proxybeam"

    PROXYBEAM_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        PROXYBEAM_ASSET_DIR / "proxybeam.png")

    def __init__(self, tower_slot):
        '''
        Initialize the Proxy Beam's range, damage, cooldown, and overlay.
        '''
        super().__init__(tower_slot)

        self.range = 150
        self.damage = 15
        self.attack_cooldown = 1400

        self.overlay_img = pygame.image.load(
            self.PROXYBEAM_ASSET_DIR / "proxybeam_overlay.png")

    def draw(self, window):
        '''
        Draw the Proxy Beam, its glow overlay, and its attack range.
        '''
        center_x, center_y = self.rect.center
        offset_center = (center_x, center_y - 5)

        image_rect = self.PROXYBEAM_IMG.get_rect(center=offset_center)

        window.blit(self.PROXYBEAM_IMG, image_rect)

        self.overlay_img.set_alpha(round(self.glow_alpha))
        window.blit(self.overlay_img, image_rect)

        self.draw_range(window)
