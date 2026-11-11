"""Aim projectiles and play their impact animations when they hit."""

# @generated fully: Projectile aiming and impact logic

from dataclasses import dataclass
from functools import lru_cache
import math
from pathlib import Path

import pygame

from .enemy.enemy import Enemy
from ....ui.sprite import Sprite


@dataclass(frozen=True)
class ProjectilePath:
    """Store a straight path and the sprite row that points along it."""

    start: tuple[float, float]
    end: tuple[float, float]
    direction: tuple[float, float]
    distance: float
    direction_row: int

    def position_at(self, distance: float) -> tuple[float, float]:
        """Return a point along the path without going past its end."""
        distance = max(0.0, min(distance, self.distance))
        return (
            self.start[0] + self.direction[0] * distance,
            self.start[1] + self.direction[1] * distance,
        )


def get_projectile_path(
    start: tuple[float, float],
    end: tuple[float, float],
) -> ProjectilePath:
    """Aim at a point; direction rows run clockwise starting with up."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    distance = math.hypot(dx, dy)
    if distance == 0:
        return ProjectilePath(start, end, (0.0, 0.0), 0.0, 0)
    angle = math.degrees(math.atan2(dx, -dy)) % 360
    # NOTE: adding 22.5 for rounding up to the nearest 45° angle
    row = int((angle + 22.5) // 45) % 8
    return ProjectilePath(
        start, end, (dx / distance, dy / distance), distance, row
    )


class Projectile(Sprite):
    """Follow a moving target and apply the shot's damage on impact."""

    def __init__(
        self,
        sheet: Path,
        start: tuple[float, float],
        target: Enemy,
        damage: int,
        speed: float,
        columns: int = 8,
        fps: int = 30,
        impact_sheet: Path | None = None,
        impact_columns: int = 6,
        impact_rows: int = 1,
        impact_fps: int = 30,
    ) -> None:
        """Load eight direction rows and keep the shot's own damage."""
        super().__init__(sheet, x_cnt=columns, y_cnt=8, fps=fps)
        self.direction_frames = [
            self.frames[row * columns:(row + 1) * columns]
            for row in range(8)
        ]
        self.target = target
        self.damage = damage
        self.speed = speed
        self.position = start
        self.finished = False
        self.impact_sheet = impact_sheet
        self.impact_columns = impact_columns
        self.impact_rows = impact_rows
        self.impact_fps = impact_fps
        self.impact = None
        self.aim_at_target()
        self.rect.center = (round(start[0]), round(start[1]))

    @staticmethod
    @lru_cache(maxsize=16)
    def get_frames(
        image: Path,
        x_cnt: int,
        y_cnt: int,
    ) -> list[pygame.Surface]:
        """Reuse loaded frames across shots."""
        return Sprite.get_frames(image, x_cnt, y_cnt)

    def aim_at_target(self) -> None:
        """Choose a direction row and path to the target's position."""
        self.path = get_projectile_path(
            self.position, (self.target.x_position, self.target.y_position)
        )
        self.frames = self.direction_frames[self.path.direction_row]
        self.image = self.frames[self.frame_index]

    def update(self, dt: float) -> int:
        """Move towards the target and return any reward from a hit."""
        if self.finished:
            return 0
        if not self.target.is_alive or self.target.reached_end:
            self.finished = True
            self.kill()
            return 0

        self.aim_at_target()
        super().update(dt)
        distance = self.speed * max(0.0, dt)
        self.position = self.path.position_at(distance)
        self.rect.center = tuple(round(value) for value in self.position)
        if distance >= self.path.distance:
            self.finished = True
            self.kill()
            reward = self.target.take_damage(self.damage)
            if self.impact_sheet is not None:
                self.impact = Impact(
                    self.impact_sheet, self.position,
                    self.impact_columns, self.impact_rows, self.impact_fps,
                )
            return reward
        return 0


class Impact(Sprite):
    """Play a hit animation once at the point where the shot arrived."""

    def __init__(
        self,
        sheet: Path,
        position: tuple[float, float],
        columns: int,
        rows: int,
        fps: int,
    ) -> None:
        """Center the effect at the hit and start at its first frame."""
        super().__init__(sheet, x_cnt=columns, y_cnt=rows, fps=fps)
        self.elapsed = 0.0
        self.rect.center = tuple(round(value) for value in position)

    @staticmethod
    def get_frames(
        image: Path,
        x_cnt: int,
        y_cnt: int,
    ) -> list[pygame.Surface]:
        """Share the projectile frame cache for repeated hit effects."""
        return Projectile.get_frames(image, x_cnt, y_cnt)

    def update(self, dt: float) -> None:
        """Advance the impact and remove it instead of looping."""
        self.elapsed += max(0.0, dt)
        frame = int(self.elapsed * self.fps)
        if frame >= len(self.frames):
            self.kill()
            return
        self.frame_index = frame
        self.image = self.frames[frame]
