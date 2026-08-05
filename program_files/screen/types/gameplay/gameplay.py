import pygame

from ...screen import Screen
from .enemy.enemy import Enemy
from ....maps.game_map import GameMap
from .tower_slot.tower_slot import TowerSlot
from .tower.tower import Tower

'''
During Gameplay when pressing P it opens up the pause menu 
Fix the event handling when introducing new towers
Figure out how to draw out the healthbar numbers properly
Font Cleanup

'''

class Gameplay(Screen): 
    MAX_HEALTH = 100
    def __init__ (self, app, selected_map): 
        super().__init__(app)
        self.game_map = selected_map

        self.wave = 1
        self.wave_cleared = False
        self.wave_cleared_delay = 1200
        self.wave_cleared_start_time = pygame.time.get_ticks()

        self.health = self.MAX_HEALTH

        self.money = 200
        self.insufficient_funds = False
        self.insufficient_funds_delay = 700
        self.insufficient_funds_start_time = 0
        
        self.towers = []
        self.load_tower_slots()
        self.selected_tower_type = None

        self.enemies = []
        self.enemies_spawned = 0
        self.enemy_wave_size = 5
        self.enemy_spawn_time = pygame.time.get_ticks()
        self.enemy_spawn_delay = 3000

        self.game_over = False

    def spawn_enemy(self): 
        self.enemies.append(Enemy(self.game_map.enemy_path)) #[TO DO] Remove Enemyself.draw_healthbar(window)
        self.enemies_spawned += 1

    def load_tower_slots(self): 
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.selected_tower_type != None: 
            if event.button == 1:

                clicked_slot = None

                for slot in self.tower_slots: 
                    if slot.rect.collidepoint(event.pos):
                        clicked_slot = slot
                        slot.selected = True
                        break

                if (clicked_slot is not None and
                    not slot.occupied and
                    slot.selected): 
                    slot.occupied = True

                    self.money -= Tower.COST
                    self.towers.append(Tower(slot))
                    self.selected_tower_type = None

                    self.cancel_tower_placement()
                else: 
                    self.cancel_tower_placement()
                    
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
                self.cancel_tower_placement()
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

#____DRAW____

    def draw(self, window):
        window.blit(self.game_map.image, (0, 0))

        for slot in self.tower_slots:
            slot.draw(window)

        for enemy in self.enemies:
            if not enemy.reached_end:
                enemy.draw(window)

        for tower in self.towers:
            tower.draw(window)
        
        self.draw_money(window)
        self.draw_healthbar(window)

        if self.insufficient_funds:
            self.draw_sufficiency(window)

        if self.selected_tower_type is not None:
            self.draw_selected_type(window)

        if self.wave_cleared: 
            self.draw_wave_cleared(window)
        
    def draw_wave_cleared(self,window): 
        font = pygame.font.Font("freesansbold.ttf", 40)
        text = font.render ("WAVE CLEARED", True, "Green")
        text_rect = text.get_rect(center = (300, 175))
        window.blit(text, text_rect)

    def draw_sufficiency(self, window):  
        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render ("INSUFFICIENT FUNDS", True, "Red")
        text_rect = text.get_rect(bottomleft = (10,340))
        window.blit(text, text_rect)

    def draw_money(self, window): 
        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render("P: " + str(self.money), True, "White")
        text_rect = text.get_rect(bottomright = (590,320))
        window.blit(text, text_rect)

    def draw_selected_type(self, window):  
        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render ("SELECTED: " + self.selected_tower_type, True, "White")
        text_rect = text.get_rect(bottomleft = (10,340))
        window.blit(text, text_rect)

    def draw_healthbar(self, window): 
        healthbar_outline = pygame.Rect(0, 0, 100, 10)
        healthbar_outline.bottomright = (590, 340)

        health = pygame.Rect(0, 0, self.health/ self.MAX_HEALTH * 100, 10)
        health.bottomleft = healthbar_outline.bottomleft

        pygame.draw.rect(window, "Yellow", health)
        pygame.draw.rect(window, "White", healthbar_outline, 1)

        font = pygame.font.Font("freesansbold.ttf", 10)
        text = font.render("♥ " + str(self.health), True, "Black")
        text_rect = text.get_rect(center = healthbar_outline.center)
        window.blit(text, text_rect)

#_____________

    def update(self, dt):
        current_time = pygame.time.get_ticks()

        if self.enemies_spawned < self.enemy_wave_size: 
            if current_time - self.enemy_spawn_time >= self.enemy_spawn_delay: 
                self.spawn_enemy()
                self.enemy_spawn_time = current_time

        for enemy in self.enemies:
            enemy.update(dt)
            if enemy.reached_end and enemy.is_alive: 
                self.health -= enemy.health
                enemy.is_alive = False

        for tower in self.towers: 
            tower.find_target(self.enemies)
            self.money += tower.attack(current_time)

        self.enemies = [
            enemy for enemy in self.enemies
            if enemy.is_alive
        ]

        if self.insufficient_funds: 
            if current_time - self.insufficient_funds_start_time >= self.insufficient_funds_delay: 
                self.insufficient_funds = False

        if self.health <= 0: 
            self.game_over = True

        if (self.enemies_spawned == self.enemy_wave_size and
            len(self.enemies) == 0 and
            not self.wave_cleared): 
            self.wave_cleared = True
            self.wave_cleared_start_time = pygame.time.get_ticks()

        if (self.wave_cleared and 
            current_time - self.wave_cleared_start_time >= self.wave_cleared_delay):
            self.wave_cleared = False

            self.wave += 1 
            self.enemies_spawned = 0
            self.enemy_spawn_time = current_time

#_________________________________________________________________

    # def draw_path(self,window):
    #     pygame.draw.lines(
    #         window, "red", False, self.game_map.enemy_path, 1
    #     )

    #     for position in self.game_map.enemy_path: 
    #         x,y = position

    #         pygame.draw.circle(
    #             window, "green", (x,y), 1
    #     )
