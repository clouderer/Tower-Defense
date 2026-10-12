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

        self.range = 90
        self.damage = 1
        self.attack_cooldown = 250

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
        Refresh living enemies within range and the target used for drawing.
        '''
        self.enemies_in_range = []

        for enemy in enemies:
            if not enemy.is_alive or enemy.reached_end:
                continue

            distance_to_enemy = math.hypot(
                enemy.x_position - self.rect.centerx,
                enemy.y_position - self.rect.centery
            )

            if distance_to_enemy <= self.range:
                self.enemies_in_range.append(enemy)

    def attack(self, current_time) -> int:
        '''
        Damage all targets once per cooldown and return their combined rewards.
        '''
        if current_time - self.last_attack_time < self.attack_cooldown:
            return 0

        enemies = [
            enemy for enemy in self.enemies_in_range
            if (
                enemy.is_alive and
                not enemy.reached_end
            )
        ]

        if not enemies:
            return 0

        self.last_attack_time = current_time
        reward = 0

        for enemy in enemies:
            enemy.health -= self.damage

            if enemy.health <= 0:
                enemy.is_alive = False
                reward += enemy.reward

        return reward
