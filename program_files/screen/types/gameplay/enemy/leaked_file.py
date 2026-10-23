"""Define the Leaked File enemy and its stats."""

from pathlib import Path
from typing import ClassVar

from .enemy import Enemy, EnemyImageSprite, EnemyLevel


class LeakedFile(Enemy):
    """Provide the stats and image for a Trojan File's spawnling."""

    # Spawnlings give no money so a surviving Trojan cannot fund towers.
    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(10, 30, 0),
        EnemyLevel(13, 33, 0),
        EnemyLevel(18, 36, 0),
        EnemyLevel(25, 39, 0),
        EnemyLevel(34, 42, 0),
        EnemyLevel(45, 46, 0),
        EnemyLevel(58, 50, 0),
        EnemyLevel(75, 53, 0),
    )

    LEAKED_FILE_IMG: ClassVar[Path] = (
        Path(__file__).resolve().parents[5]
        / "asset_files" / "leakedfile" / "leaked_file.png"
    )
    SUPPORTS_DIRECTIONS = False

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """Set the spawnling's level and load its image."""
        super().__init__(path, level)
        self.direction_sprites = {
            "default": EnemyImageSprite(self.LEAKED_FILE_IMG)
        }
        self.update_direction_sprite()
