"""Define the Trojan File enemy and its spawnling behavior."""

from pathlib import Path
from typing import ClassVar

from .enemy import Enemy, EnemyLevel
from .....ui.sprite import Sprite


class TrojanFile(Enemy):
    """Spawn Leaked Files while moving along the route."""

    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(125, 16, 18),
        EnemyLevel(190, 18, 19),
        EnemyLevel(290, 20, 20),
        EnemyLevel(440, 23, 22),
        EnemyLevel(670, 26, 24),
        EnemyLevel(1020, 29, 30),
        EnemyLevel(1550, 32, 38),
        EnemyLevel(2350, 34, 48),
    )

    SPAWNLING_INTERVALS: ClassVar[tuple[float, ...]] = (
        4.5, 4.1, 3.7, 3.3, 2.9, 2.5, 2.1, 1.8,
    )
    MAX_ACTIVE_SPAWNLINGS: ClassVar[tuple[int, ...]] = (
        2, 3, 4, 5, 6, 8, 9, 10,
    )

    TROJAN_ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[5] / "asset_files" / "trojan"
    )
    DIRECTION_SPRITES: ClassVar[dict[str, Path]] = {
        "up": TROJAN_ASSET_DIR / "trojan_up_spritesheet.png",
        "down": TROJAN_ASSET_DIR / "trojan_down_spritesheet.png",
        "left": TROJAN_ASSET_DIR / "trojan_left_spritesheet.png",
        "right": TROJAN_ASSET_DIR / "trojan_right_spritesheet.png",
    }
    SUPPORTS_DIRECTIONS = True

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """
        Load directional animations and prepare the spawnling timer.
        """
        super().__init__(path, level)
        self.direction_sprites = {
            direction: Sprite(image=sprite_path, x_cnt=4, y_cnt=2)
            for direction, sprite_path in self.DIRECTION_SPRITES.items()
        }
        self.update_direction_sprite()
        self.spawnling_timer = 0.0
        self.spawnlings_created = 0
        self.spawnling_ready = False
        self.spawnlings = []

    def update(self, dt: float) -> None:
        """
        Move the enemy and prepare a spawnling when a space is
        available.
        """
        super().update(dt)

        if self.reached_end or not self.is_alive:
            return

        self.spawnling_timer += dt
        interval = self.SPAWNLING_INTERVALS[self.level - 1]
        max_active_spawnlings = self.MAX_ACTIVE_SPAWNLINGS[self.level - 1]
        self.spawnlings = [
            spawnling for spawnling in self.spawnlings
            if spawnling.is_alive
        ]
        if len(self.spawnlings) >= max_active_spawnlings:
            self.spawnling_timer = min(self.spawnling_timer, interval)
            return

        if self.spawnling_timer >= interval:
            self.spawnling_timer -= interval
            self.spawnlings_created += 1
            self.spawnling_ready = True

    def register_spawnling(self, spawnling: Enemy) -> None:
        """Track a spawnling so it counts toward the active limit."""
        self.spawnlings.append(spawnling)

    def make_spawnling_path(self) -> list[tuple[float, float]] | None:
        """Return a route beginning at this Trojan File's position."""
        if self.reached_end:
            return None

        route = [(self.x_position, self.y_position)]
        route.extend(self.path[self.current_waypoint:])
        return route if len(route) >= 2 else None

    def consume_spawnling(self) -> list[tuple[float, float]] | None:
        """Return one spawnling route when the spawn timer is ready."""
        if not self.spawnling_ready:
            return None

        self.spawnling_ready = False
        return self.make_spawnling_path()
