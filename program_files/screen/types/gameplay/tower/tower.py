"""Handle shared tower stats, attacks, and drawing."""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import ClassVar, Optional

import pygame

from ..enemy.enemy import Enemy
from ..tower_slot.tower_slot import TowerSlot
from .....ui.sprite import Sprite
from .....ui.text_object import TextObject


@dataclass(frozen=True)
class TowerLevel:
    """Store a tower level's stats and the cost of its next upgrade."""

    range: int
    damage: int
    attack_cooldown: int
    upgrade_cost: Optional[int]

# Note: Tower was supposed to be an abstract class but for the purposes
# of testing  the Tower is non-abstract 
# For the future the Tower can be abstracted
class Tower:
    """
    Manage shared tower stats, attacks, animation, and sidebar text.
    """

    HUD_TEXT_COLOR: ClassVar[pygame.Color] = "#9feef8"
    COOLDOWN_FILL_COLOR: ClassVar[pygame.Color] = "#ff5da2"

    NAME: ClassVar[str] = "BASIC TOWER"
    COST: ClassVar[int] = 80
    RANGE_SHEETS: ClassVar[tuple[Path, ...]] = ()
    RANGE_SHEET_COLUMNS: ClassVar[int] = 6
    RANGE_SHEET_ROWS: ClassVar[int] = 4
    UPGRADE_LEVELS: ClassVar[tuple[TowerLevel, ...]] = (
        TowerLevel(70, 3, 500, 100),
        TowerLevel(80, 5, 400, 150),
        TowerLevel(90, 8, 300, None),
    )

    def __init__(self, tower_slot: TowerSlot) -> None:
        """
        Initialize tower stats, position, cooldown tracking, and target
        state.
        """
        self.image = None

        self.tower_slot = tower_slot

        # Tower position and size for drawing, clicks and range checks.
        self.rect = None

        self.level = 1
        self.total_cost = self.COST
        self.sprites = pygame.sprite.Group()
        self.underlay_sprite = None
        self.apply_level_stats()
        self.last_attack_time = pygame.time.get_ticks()

        self.target = None

        self.glow_alpha = 0

        # Tower text objects.
        self.range_text = TextObject(
            font_size=15,
            text=str(self.range) + "PX",
            color=self.HUD_TEXT_COLOR,
            anchor="topright",
            position=(588, 140)
        )

        self.damage_text = TextObject(
            font_size=15,
            text=str(self.damage),
            color=self.HUD_TEXT_COLOR,
            anchor="topright",
            position=(588, 174)
        )

        self.attack_speed_text = TextObject(
            font_size=15,
            text=str(self.attack_cooldown / 1000) + "/s",
            color=self.HUD_TEXT_COLOR,
            anchor="topright",
            position=(588, 208)
        )

        self.level_text = TextObject(
            font_size=15,
            color=self.HUD_TEXT_COLOR,
            anchor="midleft",
            position=(448, 67),
        )

        self.upgrade_cost_text = TextObject(
            font_size=12,
            color=self.HUD_TEXT_COLOR,
            anchor="midleft",
            position=(384, 295),
        )

        self.cooldown_text = TextObject(
            font_size=15,
            text="COOLDOWN",
            color=self.HUD_TEXT_COLOR,
            anchor="midleft",
            position=(384, 252),
        )
        self.cooldown_percent_text = TextObject(
            font_size=15,
            color=self.HUD_TEXT_COLOR,
            anchor="midright",
            position=(587, 252),
        )
        self.cooldown_bar_rect = pygame.Rect(384, 262, 203, 9)

    def draw(self, window: pygame.Surface) -> None:
        """Draw the tower image and its glow."""
        window.blit(self.image, self.rect)
        self.overlay_img.set_alpha(round(self.glow_alpha))
        window.blit(self.overlay_img, self.rect)

    def draw_underlay(self, window: pygame.Surface) -> None:
        """
        Draw the tower's animated underlay.

        In usual cases the underlay is a radius sprite.
        """
        self.sprites.draw(window)

    def draw_sidebar(self, window: pygame.Surface) -> None:
        """Draw the tower's stats, level, upgrade cost, and cooldown."""
        window.blit(self.sidebar, (370, 0))

        self.range_text.text = f"{self.range}PX"
        self.damage_text.text = str(self.damage)
        self.attack_speed_text.text = f"{1000 / self.attack_cooldown:.2f}/S"
        self.level_text.text = f"LEVEL {self.level}"
        self.upgrade_cost_text.text = (
            f"COST: {self.next_upgrade_cost}"
            if self.next_upgrade_cost is not None else "MAX LEVEL"
        )

        self.range_text.draw(window)
        self.damage_text.draw(window)
        self.attack_speed_text.draw(window)
        self.level_text.draw(window)
        self.upgrade_cost_text.draw(window)
        self.draw_cooldown_bar(window)

    def draw_cooldown_bar(self, window: pygame.Surface) -> None:
        """
        Draw the attack cooldown and its percentage in steps of ten.

        Step of ten is selected for improved readablity of
        the percentage.
        """
        elapsed = pygame.time.get_ticks() - self.last_attack_time
        progress = min(max(elapsed / self.attack_cooldown, 0.0), 1.0)
        percent = int(progress * 10) * 10
        self.cooldown_percent_text.text = f"{percent}%"

        pygame.draw.rect(
            window, self.HUD_TEXT_COLOR, self.cooldown_bar_rect, width=1
        )

        # Rect which holds the information for the fill Rect
        inner_rect = self.cooldown_bar_rect.inflate(-2, -2)

        filled_width = round(inner_rect.width * progress)
        if filled_width:
            fill_rect = pygame.Rect(
                inner_rect.left,
                inner_rect.top,
                filled_width,
                inner_rect.height,
            )
            pygame.draw.rect(window, self.COOLDOWN_FILL_COLOR, fill_rect)

        self.cooldown_text.draw(window)
        self.cooldown_percent_text.draw(window)

    @property
    def next_upgrade_cost(self) -> int | None:
        """
        Return the next upgrade's cost, or None at the maximum level.
        """
        if self.level >= len(self.UPGRADE_LEVELS):
            return None
        return self.UPGRADE_LEVELS[self.level - 1].upgrade_cost

    @property
    def can_upgrade(self) -> bool:
        """Check whether the tower has another level available."""
        return self.next_upgrade_cost is not None

    def upgrade(self) -> bool:
        """Apply the next level when available and report success."""
        if not self.can_upgrade:
            return False

        self.level += 1
        self.apply_level_stats()
        return True

    def apply_level_stats(self) -> None:
        """Apply the current level's stats and load its range sprite."""
        stats = self.UPGRADE_LEVELS[self.level - 1]
        self.range = stats.range
        self.damage = stats.damage
        self.attack_cooldown = stats.attack_cooldown
        self.update_range_sprite()

    def update_range_sprite(self) -> None:
        """Load this level's range sprite and center it on the slot."""
        if not self.RANGE_SHEETS:
            return

        range_sprite = Sprite(
            self.RANGE_SHEETS[self.level - 1],
            x_cnt=self.RANGE_SHEET_COLUMNS,
            y_cnt=self.RANGE_SHEET_ROWS,
        )
        range_sprite.rect.center = self.tower_slot.rect.center

        if self.underlay_sprite is not None:
            self.sprites.remove(self.underlay_sprite)
        self.underlay_sprite = range_sprite
        self.sprites.add(range_sprite)

    def update(self, dt: float) -> None:
        """Update the tower's glow and underlay animation."""
        self.update_glow(dt)
        self.sprites.update(dt)

    def update_glow(self, dt: float) -> None:
        """Fade the tower overlay in or out over a short period."""
        target_alpha = 180 if self.target is not None else 0
        difference = target_alpha - self.glow_alpha
        max_change = 300 * dt
        self.glow_alpha += max(-max_change, min(max_change, difference))

    def find_target(self, enemies: list[Enemy]) -> None:
        """Select the enemy within range that is closest to the exit."""
        enemies_in_range = []

        for enemy in enemies:
            if not enemy.is_alive or enemy.reached_end:
                continue

            distance_to_enemy = math.hypot(
                enemy.x_position - self.rect.centerx,
                enemy.y_position - self.rect.centery
            )

            if distance_to_enemy <= self.range:
                enemies_in_range.append(enemy)

        self.target = min(
            enemies_in_range,
            key=lambda enemy: enemy.distance_to_finish,
            default=None
        )

    def can_attack(self) -> bool:
        """Check whether the attack cooldown has finished."""
        current_time = pygame.time.get_ticks()
        time_since_last_attack = current_time - self.last_attack_time

        return time_since_last_attack >= self.attack_cooldown

    def attack(self, current_time: int) -> None:
        """
        Damage the target after the cooldown and return its reward if
        killed.
        """
        if (
            self.target is not None
            and self.target.is_alive
            and not self.target.reached_end
            and current_time - self.last_attack_time >= self.attack_cooldown
        ):
            self.last_attack_time = current_time
            return self.target.take_damage(self.damage)

        return 0

    def get_rect(
        self,
        center: tuple[int, int] | None = None,
    ) -> pygame.Rect:
        """
        Create a rectangle for the tower image at the given center.
        """
        if self.image is None:
            raise RuntimeError("Set the tower image before creating its rect.")

        if center is None:
            center = self.tower_slot.rect.center

        return self.image.get_rect(center=center)

    def draw_range(self, window: pygame.Surface) -> None:
        """Draw the tower's range when it has a target."""
        if self.target is not None:
            pygame.draw.circle(window, (100, 0, 0),
                               self.rect.center, self.range, 2)
