"""Provide the final boss and its temporary damage shield."""



from pathlib import Path
from typing import ClassVar

import pygame

from .enemy import Enemy, EnemyLevel
from .....ui.sprite import Sprite


class KernelPanic(Enemy):
    """Move slowly and reduce incoming damage during each shield."""

    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(20000, 6, 500),
    )
    SHIELD_INTERVAL: ClassVar[float] = 12.0
    SHIELD_DURATION: ClassVar[float] = 3.0
    SHIELD_DAMAGE_MULTIPLIER: ClassVar[float] = 0.5
    SUPPORTS_DIRECTIONS: ClassVar[bool] = True

    BOSS_ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[5] / "asset_files" / "boss"
    )
    DIRECTION_SPRITES: ClassVar[dict[str, Path]] = {
        "up": BOSS_ASSET_DIR / "up_sprite.png",
        "down": BOSS_ASSET_DIR / "down_sprite.png",
        "left": BOSS_ASSET_DIR / "left_sprite.png",
        "right": BOSS_ASSET_DIR / "right_sprite.png",
    }

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """Load the boss animations and start its shield timer."""
        super().__init__(path, level)
        self.ability_time = 0.0
        self.health_bar = pygame.Surface((44, 5), pygame.SRCALPHA)
        self.health_bar.set_alpha(self.HEALTH_BAR_ALPHA)

        self.direction_sprites = {
            direction: Sprite(image=sprite_path, x_cnt=4, y_cnt=4)
            for direction, sprite_path in self.DIRECTION_SPRITES.items()
        }
        sprite_height = max(
            sprite.rect.height for sprite in self.direction_sprites.values()
        )
        self.height = sprite_height // 2 + 6
        self.update_direction_sprite()

    @property
    def shield_active(self) -> bool:
        """Report whether the living boss is in its shield phase."""
        shield_start = self.SHIELD_INTERVAL - self.SHIELD_DURATION
        return (
            self.is_alive
            and not self.reached_end
            and self.ability_time >= shield_start
        )

    def take_damage(self, damage: int) -> int:
        """Halve shielded damage and keep the normal kill reward."""
        if self.shield_active:
            damage *= self.SHIELD_DAMAGE_MULTIPLIER
        return super().take_damage(damage)

    def update(self, dt: float) -> None:
        """Move the boss and advance its repeating shield timer."""
        if not self.is_alive or self.reached_end:
            return
        super().update(dt)
        self.ability_time = (self.ability_time + dt) % self.SHIELD_INTERVAL
