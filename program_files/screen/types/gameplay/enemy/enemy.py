"""Handle enemy health, movement, and drawing."""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import ClassVar

import pygame


class EnemyImageSprite(pygame.sprite.Sprite):
    """Display an enemy image without animation."""

    def __init__(self, image: pygame.Surface | Path) -> None:
        """
        Load an image or use a surface that has already been loaded.
        """
        super().__init__()
        if isinstance(image, pygame.Surface):
            self.image = image
        else:
            self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect()

    def update(self, dt: float) -> None:
        """Keep the image unchanged during updates."""
        pass


@dataclass(frozen=True)
class EnemyLevel:
    """Store the health, speed, and kill reward for an enemy level."""

    health: int
    speed: int
    reward: int


class Enemy:
    """Store shared enemy movement, health, and drawing behavior."""
    LEVELS: ClassVar[tuple[EnemyLevel, ...]] = (
        EnemyLevel(30, 24, 10),
    )

    DIRECTION_SPRITES: ClassVar[dict[str, object]] = {}
    SUPPORTS_DIRECTIONS: ClassVar[bool] = False
    HEALTH_BAR_ALPHA: ClassVar[int] = 140

    def __init__(
        self,
        path: list[tuple[float, float]] | tuple[tuple[float, float], ...],
        level: int = 1,
    ) -> None:
        """
        Initialize enemy stats and place the enemy at the start of its
        route.
        """

        if not 1 <= level <= len(self.LEVELS):
            raise ValueError(
                f"Enemy level must be between 1 and {len(self.LEVELS)}")

        stats = self.LEVELS[level - 1]
        self.level = level
        self.max_health = stats.health
        self.health = stats.health
        self.speed = stats.speed
        self.reward = stats.reward

        self.path = path
        self.current_waypoint = 1

        self.x_position, self.y_position = path[0]
        self.distance_to_finish = self.calculate_distance_to_finish()

        self.is_alive = True
        self.reached_end = False

        self.height = 15
        self.health_bar = pygame.Surface((20, 4), pygame.SRCALPHA)
        self.health_bar.set_alpha(self.HEALTH_BAR_ALPHA)

        self.direction = self.calculate_path_direction()
        self.sprites = pygame.sprite.Group()
        self.sprite_direction = None
        self.direction_sprites = {}

    def take_damage(self, damage: int) -> int:
        """Apply damage and return the kill reward only once."""
        if not self.is_alive or self.reached_end:
            return 0

        self.health = max(0, self.health - damage)
        if self.health == 0:
            self.is_alive = False
            return self.reward
        return 0

    def draw_health(self, window: pygame.Surface) -> None:
        """Draw a translucent bar for the enemy's remaining health."""
        self.health_bar.fill("Red")
        health_ratio = min(1, max(0, self.health / self.max_health))
        filled_width = round(health_ratio * self.health_bar.get_width())
        pygame.draw.rect(
            self.health_bar, "Green",
            (0, 0, filled_width, self.health_bar.get_height()),
        )
        health_rect = self.health_bar.get_rect(
            center=(self.x_position, self.y_position - self.height)
        )
        window.blit(self.health_bar, health_rect)

    def draw(self, window: pygame.Surface) -> None:
        """Draw the enemy and its healthbar."""
        for sprite in self.sprites:
            sprite.rect.center = (round(self.x_position),
                                  round(self.y_position))
        self.sprites.draw(window)
        self.draw_health(window)

    def update_direction_sprite(self) -> None:
        """Select a loaded sprite when the enemy changes direction."""
        if self.direction == self.sprite_direction and self.sprites:
            return

        self.sprites.empty()
        if self.SUPPORTS_DIRECTIONS:
            sprite = self.direction_sprites.get(self.direction)
        else:
            sprite = self.direction_sprites.get("default")

        sprite.rect.center = (round(self.x_position), round(self.y_position))
        self.sprites.add(sprite)
        self.sprite_direction = self.direction

    def update(self, dt: float) -> None:
        """
        Move the enemy along its route and refresh its distance to the
        finish.
        """
        if self.reached_end:
            return

        self.move(dt)
        self.sprites.update(dt)
        self.distance_to_finish = self.calculate_distance_to_finish()

    def calculate_distance(self) -> float:
        """Calculate the distance to the enemy's next waypoint."""
        target_x, target_y = self.path[self.current_waypoint]

        dx = target_x - self.x_position
        dy = target_y - self.y_position

        return math.hypot(dx, dy)

    # @generated "partially" ChatGPT 5.6 Luna:
    # Help with movement vectors.
    def move(self, dt: float) -> None:
        """
        Move along the route using all of the distance for this update.
        """
        remaining_distance = dt * self.speed

        while (
            remaining_distance > 0
            and self.current_waypoint < len(self.path)
        ):
            target_x, target_y = self.path[self.current_waypoint]
            dx = target_x - self.x_position
            dy = target_y - self.y_position
            distance = self.calculate_distance()

            if remaining_distance >= distance:
                self.x_position, self.y_position = target_x, target_y
                remaining_distance -= distance
                self.current_waypoint += 1
                self.update_direction()
            else:
                self.x_position += (dx / distance) * remaining_distance
                self.y_position += (dy / distance) * remaining_distance
                break

        if self.current_waypoint >= len(self.path):
            self.reached_end = True

    def update_direction(self) -> None:
        """Set the direction for the path segment."""
        direction = self.calculate_path_direction()
        if direction is None:
            return

        self.direction = direction
        self.update_direction_sprite()

    def calculate_path_direction(self) -> str | None:
        """
        Calculate the direction between the current pair of waypoints.
        """
        if not 0 < self.current_waypoint < len(self.path):
            return None

        previous_x, previous_y = self.path[self.current_waypoint - 1]
        next_x, next_y = self.path[self.current_waypoint]
        dx = next_x - previous_x
        dy = next_y - previous_y

        if abs(dx) >= abs(dy):
            return "right" if dx >= 0 else "left"
        return "down" if dy >= 0 else "up"

    def calculate_distance_to_finish(self) -> int:
        """Calculate the remaining distance along the route."""
        if self.current_waypoint >= len(self.path):
            return 0

        remaining_distance = self.calculate_distance()

        for i in range(self.current_waypoint, len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i + 1]

            remaining_distance += math.hypot(x2 - x1, y2 - y1)

        return int(remaining_distance)

    def draw_distance(self, window: pygame.Surface) -> None:
        """
        Draw the enemy's remaining route distance on the game window.
        """
        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render(
            "P: " + str(self.distance_to_finish), True, "Purple")
        text_rect = text.get_rect(bottomright=(590, 320))
        window.blit(text, text_rect)
