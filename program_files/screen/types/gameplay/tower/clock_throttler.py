"""Define the Clock Throttler tower."""

import math
from pathlib import Path
from typing import ClassVar


import pygame

from ..enemy.enemy import Enemy
from .....ui.sprite import Sprite
from .tower import Tower, TowerLevel


class ClockThrottler(Tower):
    """Damage all enemies within the tower's range."""
    NAME: ClassVar[str] = "CLOCK_THROTTLER"
    COST: ClassVar[int] = 350
    PULSE_IDLE_ALPHA: ClassVar[int] = 35
    PULSE_ACTIVE_ALPHA: ClassVar[int] = 160
    PULSE_FADE_SPEED: ClassVar[int] = 300
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(90, 2, 400, 175),
        TowerLevel(105, 3, 350, 550),
        TowerLevel(120, 4, 300, None),
    )

    CLOCK_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[5] / "asset_files" / "clockthrottler"
    RANGE_SHEETS: ClassVar[tuple[Path, ...]] = (
        CLOCK_ASSET_DIR / "clock_throttler_level_1_90px_sheet.png",
        CLOCK_ASSET_DIR / "clock_throttler_level_2_105px_sheet.png",
        CLOCK_ASSET_DIR / "clock_throttler_level_3_120px_sheet.png",
    )

    def __init__(self, tower_slot: "TowerSlot") -> None:
        """
        Load tower images and create the list of enemies within range.
        """
        super().__init__(tower_slot)

        self.image = pygame.image.load(
            self.CLOCK_ASSET_DIR / "clock.png")

        center_x, center_y = tower_slot.rect.center
        self.offset_center = (center_x, center_y - 3)
        self.rect = self.get_rect(center=self.offset_center)

        self.overlay_img = pygame.image.load(
            self.CLOCK_ASSET_DIR / "clock_overlay.png")

        self.sidebar = pygame.image.load(
            self.CLOCK_ASSET_DIR / "clock_sidebar.png")

        self.enemies_in_range = []
        self.pulse_sprite = Sprite(
            self.CLOCK_ASSET_DIR / "clock_throttler_pulse_sheet.png",
            x_cnt=6,
            y_cnt=10,
            fps=30,
        )
        self.pulse_alpha = float(self.PULSE_IDLE_ALPHA)

    def update(self, dt: float) -> None:
        """Keep the pulse moving and brighten it near living enemies."""
        super().update(dt)
        self.pulse_sprite.update(dt)
        enemies_in_range = any(
            enemy.is_alive and not enemy.reached_end
            for enemy in self.enemies_in_range
        )
        target_alpha = (
            self.PULSE_ACTIVE_ALPHA if enemies_in_range
            else self.PULSE_IDLE_ALPHA
        )
        difference = target_alpha - self.pulse_alpha
        max_change = self.PULSE_FADE_SPEED * dt
        self.pulse_alpha += max(-max_change, min(max_change, difference))

    def draw(self, window: pygame.Surface) -> None:
        """Draw the pulse beneath the tower, even without a target."""
        diameter = self.range * 2
        pulse_image = pygame.transform.scale(
            self.pulse_sprite.image, (diameter, diameter)
        )
        pulse_image.set_alpha(round(self.pulse_alpha))
        pulse_rect = pulse_image.get_rect(
            center=self.tower_slot.rect.center
        )
        window.blit(pulse_image, pulse_rect)
        super().draw(window)

    def find_target(self, enemies: list[Enemy]) -> None:
        """
        Find living enemies within range and select a target for
        drawing.
        """
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

        self.target = min(
            self.enemies_in_range,
            key=lambda enemy: enemy.distance_to_finish,
            default=None,
        )

    def attack(self, current_time: int) -> None:
        """
        Damage all targets after the cooldown and return their rewards.
        """
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
            reward += enemy.take_damage(self.damage)

        return reward
