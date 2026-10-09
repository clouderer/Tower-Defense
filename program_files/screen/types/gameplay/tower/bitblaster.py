import math
from typing import ClassVar
from pathlib import Path

import pygame

from .tower import Tower


class BitBlaster(Tower):
    '''
    Short-range rapid attack tower.
    '''
    NAME: ClassVar[str] = "BIT_BLASTER"
    COST: ClassVar[int] = 120

    BITBLASTER_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "bitblaster"

    BITBLASTER_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        BITBLASTER_ASSET_DIR / "bitblaster.png")

    def __init__(self, tower_slot):
        '''
        Initialize the BitBlaster's range, damage, cooldown, and overlay.
        '''
        super().__init__(tower_slot)

        self.range = 60
        self.damage = 1
        self.attack_cooldown = 130

        self.overlay_img = pygame.image.load(
            self.BITBLASTER_ASSET_DIR / "bitblaster_overlay.png")

    def draw(self, window):
        '''
        Draw the BitBlaster, its glow overlay, and its attack range.
        '''
        window.blit(self.BITBLASTER_IMG,
                    (self.tower_slot.x_pos, self.tower_slot.y_pos))

        self.overlay_img.set_alpha(round(self.glow_alpha))
        window.blit(self.overlay_img,
                    (self.tower_slot.x_pos, self.tower_slot.y_pos))

        self.draw_range(window)
