import pygame
import math

from abc import ABC, abstractmethod
from ..tower_slot.tower_slot import TowerSlot
from ..enemy.enemy import Enemy

class Tower: 
    NAME = "BASIC TOWER"
    COST = 80

    def __init__(self, tower_slot):
        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = tower_slot.rect.center

        self.range  = 70
        self.damage = 3
        self.attack_cooldown = 500
        self.last_attack_time = pygame.time.get_ticks() 

        self.target = None

    def draw(self, window): 
        pygame.draw.rect(window, "pink", self.rect)

        if self.target is not None:
            pygame.draw.circle(window, (100, 0, 0), self.rect.center, self.range, 2)

    def find_target(self, enemies):
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
    def can_attack(self):
        current_time = pygame.time.get_ticks()
        time_since_last_attack = current_time - self.last_attack_time

        return time_since_last_attack >= self.attack_cooldown
    
    def attack(self, current_time): 
        if (self.target is not None and 
            current_time - self.last_attack_time >= self.attack_cooldown): 
                self.target.health -= self.damage
                self.last_attack_time = current_time

                if self.target.health <= 0: 
                    self.target.is_alive = False
                    return self.target.reward

        return 0
        

