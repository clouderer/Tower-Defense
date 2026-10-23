# from pathlib import Path 
# from typing import ClassVar

# import pygame 
# from .enemy import Enemy, EnemyLevel
# from .....ui.sprite import Sprite

# class Boss(Enemy): 

#     # [TO DO] - try out different values 
#     LEVELS: ClassVar[tuple[EnemyLevel, ...]] = ( 
#         EnemyLevel(1000, 25, 0),
#     )

#     BOSS_ASSET_DIR: ClassVar[Path] = ( 
#         Path(__file__).resolve().parents[5] / "asset_files" / "boss"
#     )

#     DIRECTION_SPRITES: ClassVar[dict[str, Path]] = { 
#         "up": BOSS_ASSET_DIR / "up_spritesheet.png", 
#         "down": BOSS_ASSET_DIR / "down_spritesheet.png",
#         "left": BOSS_ASSET_DIR / "left_spritesheet.png",
#         "right": BOSS_ASSET_DIR / "right_spritesheet.png",
#     }

#     SUPPORTS_DIRECTIONS = True

#     # [TO DO] - try out different values for shield cooldown 
#     SHIELD_COOLDOWN: ClassVar[int] = 2000

#     def __init__(self, path, level=1):
#         """Set the enemy's level and load its directional animations."""
#         super().__init__(path, level)
#         self.direction_sprites = {
#             direction: Sprite(
#                 image=sprite_path,
#                 x_cnt=8,
#                 y_cnt=1,
#             )
#             for direction, sprite_path in self.DIRECTION_SPRITES.items()
#         }
#         self.update_direction_sprite()

#         # [TO DO] - make shield
#         self.shield_sprite = Sprite(self.BOSS_ASSET_DIR / "shield" , )

#     def apply_shield(self): 
#         """Enemy shields himself and stops taking damage.
        
#             When the enemy is shielded the enemy becomes slightly slower.
#         """
#         pass
"""Define the boss enemy and its shield behavior."""

