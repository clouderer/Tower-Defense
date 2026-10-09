import math

from typing import ClassVar
from pathlib import Path

import pygame

from .tower import Tower


class ClockThrottler(Tower):
    '''
    Mid-range tower that damages enemies within its range.
    '''
    NAME: ClassVar[str] = "CLOCK_THROTTLER"
    COST: ClassVar[int] = 350

    CLOCK_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "clockthrottler"

    CLOCK_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        CLOCK_ASSET_DIR / "clock.png")

    def __init__(self, tower_slot):
        '''
        Initialize tower stats, overlay image, and in-range enemy list.
        '''
        super().__init__(tower_slot)

        self.range = 100
        self.damage = 0.0005
        self.attack_cooldown = 15

        self.overlay_img = pygame.image.load(
            self.CLOCK_ASSET_DIR / "clock_overlay.png")

        self.enemies_in_range = []

    def draw(self, window):
        '''
        Draw the tower, its glow overlay, and its attack range.
        '''
        center_x, center_y = self.rect.center
        offset_center = (center_x, center_y - 3)

        image_rect = self.CLOCK_IMG.get_rect(center=offset_center)

        window.blit(self.CLOCK_IMG, image_rect)

        self.overlay_img.set_alpha(round(self.glow_alpha))
        window.blit(self.overlay_img, image_rect)

        self.draw_range(window)

    def find_target(self, enemies):
        '''
        Add living enemies within range to the list of targets.
        '''
        for enemy in enemies:
            if not enemy.is_alive or enemy.reached_end:
                continue

            distance_to_enemy = math.hypot(
                enemy.x_position - self.rect.centerx,
                enemy.y_position - self.rect.centery
            )

        # [TO DO] Check how many enemies are in the area - apply
            if distance_to_enemy <= self.range:
                self.enemies_in_range.append(enemy)

    def attack(self, current_time):
        '''
        Damage enemies in range and return the reward if an enemy is defeated.
        '''
        if self.enemies_in_range is []:
            return 0

        enemies = [
            enemy for enemy in self.enemies_in_range
            if (
                enemy.is_alive and
                not enemy.reached_end
            )
        ]

        for enemy in enemies:
            enemy.health -= self.damage
            self.last_attack_time = current_time

            if enemy.health <= 0:
                enemy.is_alive = False
                return enemy.reward

        return 0
