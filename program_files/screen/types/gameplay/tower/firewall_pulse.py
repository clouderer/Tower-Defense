from typing import ClassVar
from pathlib import Path

import pygame

from .tower import Tower


class FirewallPulse(Tower):
    NAME: ClassVar[str] = "FIREWALL_PULSE"
    COST: ClassVar[int] = 100

    FIREWALL_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "firewallpulse"

    FIREWALL_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        FIREWALL_ASSET_DIR / "firewall.png")

    def __init__(self, tower_slot):
        '''
        Initialize the Firewall Pulse's range, damage, cooldown, and overlay.
        '''
        super().__init__(tower_slot)

        self.range = 60
        self.damage = 3
        self.attack_cooldown = 300

        self.overlay_img = pygame.image.load(
            self.FIREWALL_ASSET_DIR / "firewall_overlay.png")

    def draw(self, window):
        '''
        Draw the Firewall Pulse, its glow overlay, and its attack range.
        '''
        center_x, center_y = self.rect.center
        offset_center = (center_x, center_y)

        image_rect = self.FIREWALL_IMG.get_rect(center=offset_center)

        window.blit(self.FIREWALL_IMG, image_rect)

        self.overlay_img.set_alpha(round(self.glow_alpha))
        window.blit(self.overlay_img, image_rect)

        self.draw_range(window)
