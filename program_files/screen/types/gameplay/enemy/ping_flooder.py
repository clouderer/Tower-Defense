"""Define the Ping Flooder enemy and its stats."""

from pathlib import Path
from typing import ClassVar

from .enemy import Enemy, EnemyLevel, EnemyImageSprite


class PingFlooder(Enemy):
    """
    Provide the stats and images for the fast enemy with low health.
    """

    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(16, 60, 2),
        EnemyLevel(24, 68, 2),
        EnemyLevel(36, 77, 2),
        EnemyLevel(54, 86, 3),
        EnemyLevel(80, 96, 3),
        EnemyLevel(120, 106, 4),
        EnemyLevel(175, 117, 5),
        EnemyLevel(250, 128, 6),
    )

    PING_ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[5] / "asset_files" / "ping"
    )
    DIRECTION_SPRITES: ClassVar[dict[str, Path]] = {
        "up": PING_ASSET_DIR / "ping_up.png",
        "down": PING_ASSET_DIR / "ping_down.png",
        "left": PING_ASSET_DIR / "ping_left.png",
        "right": PING_ASSET_DIR / "ping_right.png",
    }
    SUPPORTS_DIRECTIONS = True

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """Set the enemy's level and load its directional images."""
        super().__init__(path, level)
        self.direction_sprites = {
            direction: EnemyImageSprite(image_path)
            for direction, image_path in self.DIRECTION_SPRITES.items()
        }
        self.update_direction_sprite()
