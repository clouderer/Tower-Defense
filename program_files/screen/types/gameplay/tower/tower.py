import math
from typing import ClassVar
from pathlib import Path

import pygame

from ..tower_slot.tower_slot import TowerSlot
from ..enemy.enemy import Enemy


class Tower:
    NAME: ClassVar[str] = "BASIC TOWER"
    COST: ClassVar[int] = 80

    def __init__(self, tower_slot):
        '''
        Initialize tower stats, position, cooldown tracking, and target state.
        '''
        self.image = None  # Tower image

        self.level = 1

        self.tower_slot = tower_slot
        self.rect = pygame.Rect(0, 0, 10, 10)
        self.rect.center = tower_slot.rect.center

        self.range = 70
        self.damage = 3
        self.attack_cooldown = 500
        self.last_attack_time = pygame.time.get_ticks()

        self.target = None

        self.glow_alpha = 0

    def draw(self, window):
        '''
        Draw the base tower placeholder.
        '''
        pygame.draw.rect(window, "Blue", self.rect)

    def draw_range(self, window):
        '''
        If an enemy is in range, draws the range out.
        '''
        if self.target is not None:
            pygame.draw.circle(window, (100, 0, 0),
                               self.rect.center, self.range, 2)

    def update(self, dt):
        '''
        Update the tower's glow animation.
        '''
        self.update_glow(dt)

    def update_glow(self, dt):
        '''
        Fade the tower overlay in or out over a short period.
        '''
        target_alpha = 180 if self.target is not None else 0
        difference = target_alpha - self.glow_alpha
        max_change = 300 * dt
        self.glow_alpha += max(-max_change, min(max_change, difference))

    # [TO DO] Add a helper that checks whether an enemy is in range.

    def find_target(self, enemies):
        '''
        Sets the Towers target.
        '''
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
        '''
        Tracks the towers attack cooldown.
        '''
        current_time = pygame.time.get_ticks()
        time_since_last_attack = current_time - self.last_attack_time

        return time_since_last_attack >= self.attack_cooldown

    def attack(self, current_time) -> int:
        '''
        Damage the target, update its state, and return any reward earned.
        '''
        if (
            self.target is not None
            and current_time - self.last_attack_time >= self.attack_cooldown
        ):
            self.target.health -= self.damage
            self.last_attack_time = current_time

            if not self.target.health <= 0:
                self.target.is_alive = False
                return self.target.reward

        return 0
