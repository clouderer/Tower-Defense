"""Define the Glitchworm enemy and its stats."""

from pathlib import Path
from typing import ClassVar

from .enemy import Enemy, EnemyLevel
from .....ui.sprite import Sprite


class Glitchworm(Enemy):
    """Provide the health, speed, and sprites for the basic enemy."""

    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(55, 25, 10),
        EnemyLevel(85, 28, 10),
        EnemyLevel(130, 31, 11),
        EnemyLevel(210, 34, 12),
        EnemyLevel(340, 37, 13),
        EnemyLevel(550, 40, 17),
        EnemyLevel(850, 43, 23),
        EnemyLevel(1250, 46, 31),
    )

    GLITCHWORM_ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[5] / "asset_files" / "worm"
    )

    DIRECTION_SPRITES: ClassVar[dict[str, Path]] = {
        "up": GLITCHWORM_ASSET_DIR / "up_spritesheet.png",
        "down": GLITCHWORM_ASSET_DIR / "down_spritesheet.png",
        "left": GLITCHWORM_ASSET_DIR / "left_spritesheet.png",
        "right": GLITCHWORM_ASSET_DIR / "right_spritesheet.png",
    }
    SUPPORTS_DIRECTIONS = True

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """Set the enemy's level and load its directional animations."""
        super().__init__(path, level)
        self.direction_sprites = {
            direction: Sprite(
                image=sprite_path,
                x_cnt=8,
                y_cnt=1,
                fps=13,
            )
            for direction, sprite_path in self.DIRECTION_SPRITES.items()
        }
        self.update_direction_sprite()
