import pygame 

class TowerSlot: 
    def __init__(self, position): 
        self.x_position, self.y_position = position
        self.rect = pygame.Rect(self.x_position, self.y_position, 24, 24)

        self.occupied = False 
        self.selected = False
        self.hovering = False

    def draw(self, window):
        if self.occupied and self.hovering:
            color = "Red"
        elif self.occupied and self.selected: 
            color = "White"
        elif self.selected:
            color = "Green"
        elif self.hovering:
            color = "Yellow"
        else:
            color = "White"
        
        pygame.draw.rect(window, color, self.rect)