import pygame

from abc import ABC, abstractmethod
from ..tower_slot.tower_slot import TowerSlot

class Tower: 
    def __init__(self, tower_slot):

        self.rect = pygame.Rect(0, 0, 20, 20)
        self.rect.center = tower_slot.rect.center

    def draw(self, window): 
        pygame.draw.rect(window, "pink", self.rect)

