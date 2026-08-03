import pygame

from ...screen import Screen
from .enemy.enemy import Enemy
from ....maps.game_map import GameMap
from .tower_slot.tower_slot import TowerSlot
from .tower.tower import Tower

'''
During Gameplay when pressing escape it opens up the pause menu 


'''

MAX_HEALTH = 100

class Gameplay(Screen): 
    def __init__ (self, app, selected_map): 
        super().__init__(app)
        self.game_map = selected_map

        self.current_health = MAX_HEALTH
        
        self.towers = []
        self.load_tower_slots()

        self.selected_tower_type = None

        self.enemies = []
        self.enemy = Enemy(self.game_map.enemy_path) #[TO DO] Remove Enemy

    def load_tower_slots(self): 
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.selected_tower_type != None: 
            if event.button == 1:
                for slot in self.tower_slots: 
                    slot.selected = slot.rect.collidepoint(event.pos)

                    if not slot.occupied and slot.selected: 
                        slot.occupied = True
                        self.towers.append(Tower(slot))
                    else: 
                        continue
                    
        if event.type == pygame.MOUSEMOTION and self.selected_tower_type != None: 
            for slot in self.tower_slots: 
                slot.hovering = slot.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_1 or event.key == pygame.K_KP1: 
                self.selected_tower_type = Tower
            if event.key == pygame.K_ESCAPE:
                self.selected_tower_type = None
            if event.key == pygame.K_p: 
                pass #[TO DO] Pause
        """
        [TO DO]: 
        EXPECTABLE BEHAVIOR 
            Tower actions
                Place Tower 
                Upgrade Tower 
                Remove Tower 
            View Enemy Health 
            Skip Wave 
            Pause 
                Reach Settings 
            Quit 
        """

    def draw(self, window):
        window.blit(self.game_map.image, (0, 0))
        # self.draw_path(window)

        for slot in self.tower_slots:
            slot.draw(window)

        if not self.enemy.reached_end:
            self.enemy.draw(window)

        for tower in self.towers:
            tower.draw(window)

        if self.enemy.reached_end:
            #[TO DO] - give the CPU damage equivalent to the health of the enemy
            font = pygame.font.Font("freesansbold.ttf", 32)
            text = font.render("GAME OVER", True, "white")
            text_rect = text.get_rect(center=(300, 175))
            window.blit(text, text_rect)

    def draw_path(self,window):
        pygame.draw.lines(
            window, "red", False, self.game_map.enemy_path, 1
        )

        for position in self.game_map.enemy_path: 
            x,y = position

            pygame.draw.circle(
                window, "green", (x,y), 1
        )


    def update(self, dt):
        self.enemy.update(dt)