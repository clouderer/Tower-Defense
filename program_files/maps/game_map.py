"""
Good idea would be to have maps with different sizes
for our purposes all maps will have the same diemsnions: 

    350x600  <--- This size was selected as optimal by me 
    
    It is large enough for the game, and small enough to have it as a little
    side window
"""

from pathlib import Path

import pygame


# Map definitions
MAP_ASSET_DIR = Path(__file__).resolve().parents[2] / "asset_files" / "maps"

NEON_GRID_PATH = (
    (1, 176),
    (26, 176),
    (26, 76),
    (126, 76),
    (126, 176),
    (76, 176),
    (76, 276),
    (226, 276),
    (226, 176),
    (176, 176),
    (176, 76),
    (326, 76),
    (326, 176),
    (276, 176),
    (276, 276),
    (426, 276),
    (426, 176),
    (376, 176),
    (376, 76),
    (526, 76),
    (526, 201),
)

NEON_GRID_TOWER_POSITIONS = (
    (51, 101),
    (76, 101),
    (51, 126),
    (76, 126),
    (101, 201),
    (126, 201),
    (151, 201),
    (176, 201),
    (101, 226),
    (126, 226),
    (151, 226),
    (176, 226),
    (201, 101),
    (226, 101),
    (251, 101),
    (276, 101),
    (201, 126),
    (226, 126),
    (251, 126),
    (276, 126),
    (301, 26),
    (326, 26),
    (351, 26),
    (376, 26),
    (401, 26),
    (301, 201),
    (326, 201),
    (351, 201),
    (376, 201),
    (301, 226),
    (326, 226),
    (351, 226),
    (376, 226),
    (401, 101),
    (426, 101),
    (451, 101),
    (476, 101),
    (401, 126),
    (426, 126),
    (451, 126),
    (476, 126),
    (451, 201),
    (451, 226),
    (451, 251),
)

class GameMap:
    def __init__(self, image, enemy_path, tower_positions):
        self.image = image
        self.width, self.height = image.get_size()

        self.enemy_path = enemy_path
        self.spawn_position = enemy_path[0]
        self.exit_position = enemy_path[-1]

        self.tower_positions = tower_positions


NEON_GRID_MAP = GameMap(
    pygame.image.load(MAP_ASSET_DIR / "neon_grid.png"),
    NEON_GRID_PATH,
    NEON_GRID_TOWER_POSITIONS,
)
