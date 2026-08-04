import pygame

from ...screen import Screen
from .enemy.enemy import Enemy
from ....maps.game_map import GameMap
from .tower_slot.tower_slot import TowerSlot
from .tower.tower import Tower

'''
During Gameplay when pressing escape it opens up the pause menu 
Figure out how to draw out insuffcicent funds when placing or upgrading towers
Fix the event handling when introducing new towers


'''

MAX_HEALTH = 100

class Gameplay(Screen): 
    def __init__ (self, app, selected_map): 
        super().__init__(app)
        self.game_map = selected_map

        self.current_health = MAX_HEALTH

        self.money = 100
        self.insufficient_funds = False
        self.insufficient_funds_delay = 700
        self.insufficient_funds_start_time = 0
        
        self.towers = []
        self.load_tower_slots()

        self.selected_tower_type = None

        self.enemies = []
        self.enemy_spawn_time = pygame.time.get_ticks()
        self.enemy_spawn_delay = 3000

    def make_enemy(self): 
        self.enemies.append(Enemy(self.game_map.enemy_path)) #[TO DO] Remove Enemy

    def load_tower_slots(self): 
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.selected_tower_type != None: 
            if event.button == 1:
                for slot in self.tower_slots: 
                    tower = Tower(slot)

                    slot.selected = slot.rect.collidepoint(event.pos)

                    if not slot.occupied and slot.selected: 
                        self.money -= tower.COST
                        slot.occupied = True
                        self.towers.append(tower)
                        self.selected_tower_type = None
                    else: 
                        self.cancel_tower_placement()
                        self.selected_tower_type = None
                    
        if event.type == pygame.MOUSEMOTION and self.selected_tower_type != None: 
            for slot in self.tower_slots: 
                slot.hovering = slot.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN: 
            if event.key == pygame.K_1 or event.key == pygame.K_KP1: 
                if self.money >= Tower.COST: 
                    self.insufficient_funds = False
                    self.selected_tower_type = Tower.NAME
                else: 
                    self.insufficient_funds = True
                    self.insufficient_funds_start_time = pygame.time.get_ticks()
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                pass #[TO DO] 
            elif event.key == pygame.K_3 or event.key == pygame.K_KP3: 
                pass #[TO DO] 
            elif event.key == pygame.K_4 or event.key == pygame.K_KP4: 
                pass #[TO DO] 


            elif event.key == pygame.K_ESCAPE:
                self.selected_tower_type = None
            elif event.key == pygame.K_p: 
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
    def cancel_tower_placement(self):
        self.selected_tower_type = None 

        for slot in self.tower_slots: 
            slot.selected = slot.hovering = False

    def draw(self, window):
        window.blit(self.game_map.image, (0, 0))

        for slot in self.tower_slots:
            slot.draw(window)

        for enemy in self.enemies:
            if not enemy.reached_end:
                enemy.draw(window)

            if enemy.reached_end:
                #[TO DO] - give the CPU damage equivalent to the health of the enemy
                font = pygame.font.Font("freesansbold.ttf", 32)
                text = font.render("GAME OVER", True, "White")
                text_rect = text.get_rect(center=(300, 175))
                window.blit(text, text_rect)

        for tower in self.towers:
            tower.draw(window)
        
        self.selected_type(window)
        self.draw_money(window)
        self.draw_sufficiency(window)

    def draw_sufficiency(self, window): 
        if self.insufficient_funds: 
            font = pygame.font.Font("freesansbold.ttf", 10)
            text = font.render ("INSUFFICIENT FUNDS", True, "Red")
            text_rect = text.get_rect(bottomleft = (10,340))
            window.blit(text, text_rect)

    def draw_money(self, window): 
        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render("P: " + str(self.money), True, "White")
        text_rect = text.get_rect(bottomright = (590,340))
        window.blit(text, text_rect)

    def selected_type(self, window): 
        if self.selected_tower_type != None: 
            font = pygame.font.Font("freesansbold.ttf", 10)
            text = font.render ("SELECTED: " + self.selected_tower_type, True, "White")
            text_rect = text.get_rect(bottomleft = (10,340))
            window.blit(text, text_rect)

    def update(self, dt):
        current_time = pygame.time.get_ticks()

        if len(self.enemies) < 3: 
            if current_time - self.enemy_spawn_time >= self.enemy_spawn_delay: 
                self.make_enemy()
                self.enemy_spawn_time = current_time

        for enemy in self.enemies:
            enemy.update(dt)

        if self.insufficient_funds: 
            if current_time - self.insufficient_funds_start_time >= self.insufficient_funds_delay: 
                self.insufficient_funds = False
#_________________________________________________________________

    def draw_path(self,window):
        pygame.draw.lines(
            window, "red", False, self.game_map.enemy_path, 1
        )

        for position in self.game_map.enemy_path: 
            x,y = position

            pygame.draw.circle(
                window, "green", (x,y), 1
        )
