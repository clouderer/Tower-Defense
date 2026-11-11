"""Draw a sustained beam between a tower and its target."""

import math
from pathlib import Path
from typing import ClassVar

import pygame

from .enemy.enemy import Enemy
from .projectile import Projectile, get_projectile_path


class Beam:
    """Keep an animated emitter and hit effect joined by a laser."""

    GLOW_COLOR: ClassVar[str] = "#70dfd8"
    INNER_COLOR: ClassVar[str] = "#c6fff5"
    CORE_COLOR: ClassVar[str] = "#ffffff"
    FADE_DURATION: ClassVar[float] = 0.08

    def __init__(
        self,
        start: tuple[float, float],
        target: Enemy,
        max_range: float,
        emitter_sheet: Path,
        impact_sheet: Path,
        duration: float = 0.78,
        fps: int = 30,
    ) -> None:
        """Connect both ends and load their animation frames."""
        self.start = start
        self.target = target
        self.max_range = max_range
        self.duration = duration
        self.fps = fps
        
        self.elapsed = 0.0
        self.fade_elapsed: float | None = None
        self.finished = False
        self.end = (target.x_position, target.y_position)
        
        self.emitter_frames = Projectile.get_frames(emitter_sheet, 8, 1)
        self.impact_frames = Projectile.get_frames(impact_sheet, 8, 1)

    @property
    def alpha(self) -> int:
        """Fade at the end of the burst or after losing the target."""
        fade = (self.duration - self.elapsed) / self.FADE_DURATION
        if self.fade_elapsed is not None:
            fade = min(fade, 1 - self.fade_elapsed / self.FADE_DURATION)
        return round(255 * max(0.0, min(1.0, fade)))

    def update(self, dt: float) -> None:
        """Follow the enemy and fade when the connection is lost."""
        if self.finished:
            return
        dt = max(0.0, dt)
        self.elapsed += dt
        endpoint = (self.target.x_position, self.target.y_position)
        path = get_projectile_path(self.start, endpoint)
        connected = (
            self.target.is_alive and not self.target.reached_end
            and path.distance <= self.max_range
        )
        if connected and self.fade_elapsed is None:
            self.end = endpoint
        else:
            if self.fade_elapsed is None:
                self.fade_elapsed = 0.0
            self.fade_elapsed += dt
        if self.elapsed >= self.duration or self.alpha == 0:
            self.finished = True

    def draw(self, window: pygame.Surface) -> None:
        """Draw a full beam with animated effects at both ends."""
        if self.finished:
            return
        start = tuple(round(value) for value in self.start)
        end = tuple(round(value) for value in self.end)
        left, top = min(start[0], end[0]) - 8, min(start[1], end[1]) - 8
        size = (abs(end[0] - start[0]) + 17,
                abs(end[1] - start[1]) + 17)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        local_start = (start[0] - left, start[1] - top)
        local_end = (end[0] - left, end[1] - top)
        shimmer = 0.9 + 0.1 * math.sin(self.elapsed * 45)
        for value, width, opacity in (
            (self.GLOW_COLOR, 7, 0.25 * shimmer),
            (self.INNER_COLOR, 3, 0.8),
            (self.CORE_COLOR, 1, 1.0),
        ):
            color = pygame.Color(value)
            color.a = round(self.alpha * opacity)
            pygame.draw.line(surface, color, local_start, local_end, width)
        window.blit(surface, (left, top))
        frame_index = int(self.elapsed * self.fps)
        for frames, position in (
            (self.emitter_frames, start), (self.impact_frames, end),
        ):
            image = frames[frame_index % len(frames)].copy()
            image.set_alpha(self.alpha)
            window.blit(image, image.get_rect(center=position))
