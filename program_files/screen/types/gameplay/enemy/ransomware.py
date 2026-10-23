"""Define the Ransomware enemy and its stats."""

from pathlib import Path
from typing import ClassVar

from .enemy import Enemy, EnemyLevel
from .....ui.sprite import Sprite


class Ransomware(Enemy):
    """
    Provide the health, speed, and sprites for the slow tank enemy.
    """

    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(205, 10, 20),
        EnemyLevel(310, 12, 22),
        EnemyLevel(480, 14, 24),
        EnemyLevel(750, 16, 27),
        EnemyLevel(1150, 19, 30),
        EnemyLevel(1750, 22, 38),
        EnemyLevel(2600, 25, 48),
        EnemyLevel(3800, 28, 60),
    )
    SUPPORTS_DIRECTIONS = True

    RANSOMWARE_ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[5] / "asset_files" / "tank"
    )
    DIRECTION_SPRITES: ClassVar[dict[str, Path]] = {
        "up": RANSOMWARE_ASSET_DIR / "tank_sprite_up.png",
        "down": RANSOMWARE_ASSET_DIR / "tank_sprite_down.png",
        "left": RANSOMWARE_ASSET_DIR / "tank_sprite_left.png",
        "right": RANSOMWARE_ASSET_DIR / "tank_sprite_right.png",
    }

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """Set the enemy's level and load its directional animations."""
        super().__init__(path, level)
        self.direction_sprites = {
            direction: Sprite(image=image_path, x_cnt=4, y_cnt=1)
            for direction, image_path in self.DIRECTION_SPRITES.items()
        }
        self.update_direction_sprite()
