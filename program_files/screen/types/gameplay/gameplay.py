from dataclasses import dataclass, field
from typing import ClassVar  # Shared by all classes, like a static attribute.

import pygame

from ....maps.game_map import GameMap
from ....ui.text_object import TextObject
from ...screen import Screen
from .enemy.enemy import Enemy
from .tower.tower import Tower
from .tower_slot.tower_slot import TowerSlot

'''
During Gameplay when pressing P it opens up the pause menu 
Fix the event handling when introducing new towers
Figure out how to draw out the healthbar numbers properly
Font Cleanup
Probably cleanup the draw function

'''
# _____UNUSED____

'''Helping Structure for Wave attributes'''

@dataclass
class WaveState:
    CLEARED_DELAY: ClassVar[int] = 1200

    round: int = 1
    active: bool = False
    cleared: bool = False
    cleared_start_time: int = None

    next_ready = True

    max_enemy_count: int = 5

# [TO DO] Apply the enemy state to the gameplay class, and make it so that the enemies are spawned from the enemy state instead of the gameplay class.
@dataclass
class EnemyState:
    SPAWN_DELAY: ClassVar[int] = 3000

    enemies: list[Enemy] = field(default_factory=list)
    count: int = 0
    spawn_time: int = 0

class Gameplay(Screen):
    MAX_HEALTH = 100

    def __init__(self, app, selected_map):
        super().__init__(app)
        self.game_map = selected_map

        self.wave_state = WaveState()

        self.health = self.MAX_HEALTH

        self.game_over = False

        self.money = 200
        self.insufficient_funds = False
        self.insufficient_funds_delay = 700
        self.insufficient_funds_start_time = 0
        
        self.towers = []
        self.load_tower_slots()
        self.selected_tower_type = None

        self.enemy_state = EnemyState()

        # Drawable Text Objects
        self.wave_ready_text = TextObject(
            text="Press [Space] to start wave " + str(self.wave_state.round),
            color="Yellow",
            position=(300, 335),
        )

        self.wave_cleared_text = TextObject(
            text="WAVE " + str(self.wave_state.round) + " CLEARED",
            color="Green",
            position=(300, 175),
            font_size=40,
        )

        self.game_over_text = TextObject(
            text="GAME OVER",
            color="Red",
            position=(300, 175),
            font_size=40,
        )

        self.restart_text = TextObject(
            text="Press [R] to restart",
            color="Yellow",
            position=(300, 210),
            font_size=13,
        )

        self.money_text = TextObject(
            text="⌁: " + str(self.money),
            color="White",
            anchor="bottomright",
            position=(590, 320),
            font_size=10,
        )

        self.sufficiency_text = TextObject(
            text="INSUFFICIENT FUNDS",
            color="Red",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

        self.selected_tower_type_text = TextObject(
            text="SELECTED: " + self.selected_tower_type.NAME if self.selected_tower_type else "",
            color="White",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

    def spawn_enemy(self):
        self.enemy_state.enemies.append(
            Enemy(self.game_map.enemy_path)
        )
        self.enemy_state.count += 1

    def load_tower_slots(self):
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.app.change_screen(Gameplay(self.app, self.game_map))
            return
        
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and self.selected_tower_type is not None
        ):
            if event.button == 1:

                clicked_slot = None

                for slot in self.tower_slots:
                    if slot.rect.collidepoint(event.pos):
                        clicked_slot = slot
                        slot.selected = True
                        break

                if clicked_slot is not None and not clicked_slot.occupied:
                    clicked_slot.occupied = True

                    self.money -= Tower.COST
                    self.towers.append(self.selected_tower_type(clicked_slot))
                    self.selected_tower_type = None

                    self.cancel_tower_placement()
                else:
                    self.cancel_tower_placement()

        if (
            event.type == pygame.MOUSEMOTION
            and self.selected_tower_type is not None
        ):
            for slot in self.tower_slots:
                slot.hovering = slot.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 or event.key == pygame.K_KP1:
                if self.money >= Tower.COST:
                    self.insufficient_funds = False
                    self.selected_tower_type = Tower
                else:
                    self.insufficient_funds = True
                    self.insufficient_funds_start_time = pygame.time.get_ticks()
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                pass  # [TO DO]
            elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                pass  # [TO DO]
            elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                pass  # [TO DO]

            elif event.key == pygame.K_ESCAPE:
                self.cancel_tower_placement()
            elif event.key == pygame.K_p:
                pass  # [TO DO] Pause
            elif event.key == pygame.K_SPACE and self.wave_state.next_ready:
                self.wave_state.active = True
                self.wave_state.next_ready = False
                self.enemy_spawn_time = pygame.time.get_ticks()

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

# ____DRAW____

    def draw(self, window):
        window.blit(self.game_map.image, (0, 0))

        # [TO DO] Create a list for all the objects that always need to be drawn, like the tower slots and towers, and draw them in a loop.

        for slot in self.tower_slots:
            slot.draw(window)

        for enemy in self.enemy_state.enemies:
            if not enemy.reached_end:
                enemy.draw(window)

        for tower in self.towers:
            tower.draw(window)
        
        self.draw_money(window)
        self.draw_healthbar(window)

        if self.insufficient_funds and not self.wave_state.cleared:
            self.sufficiency_text.draw(window)

        if self.selected_tower_type is not None and not self.wave_state.cleared:
            self.draw_selected_type(window)

        if self.game_over:
            self.draw_game_over(window)
        elif self.wave_state.cleared:
            self.draw_wave_cleared(window)
        elif self.wave_state.next_ready:
            self.draw_wave_ready(window)

    def draw_wave_ready(self, window):
        self.wave_ready_text.text = "Press [Space] to start wave " + str(self.wave_state.round)
        self.wave_ready_text.draw(window)

    def draw_game_over(self, window):
        self.game_over_text.draw(window)
        self.restart_text.draw(window)

    def draw_wave_cleared(self, window):
        self.wave_cleared_text.text = "WAVE " + str(self.wave_state.round) + " CLEARED"
        self.wave_cleared_text.draw(window)

    def draw_money(self, window):
        self.money_text.text = "POWER: " + str(self.money)
        self.money_text.draw(window)

    def draw_selected_type(self, window):
        self.selected_tower_type_text.text = "SELECTED: " + self.selected_tower_type.NAME
        self.selected_tower_type_text.draw(window)

    def draw_healthbar(self, window):
        healthbar_outline = pygame.Rect(0, 0, 100, 10)
        healthbar_outline.bottomright = (590, 340)

        health = pygame.Rect(0, 0, self.health / self.MAX_HEALTH * 100, 10)
        health.bottomleft = healthbar_outline.bottomleft

        pygame.draw.rect(window, "Yellow", health)
        pygame.draw.rect(window, "White", healthbar_outline, 1)

# _____________
    def update_enemy_spawn(self, current_time):
        if not self.wave_state.active:
            return

        if self.enemy_state.count >= self.wave_state.max_enemy_count:
            return

        if current_time - self.enemy_state.spawn_time < self.enemy_state.SPAWN_DELAY:
            return

        self.spawn_enemy()
        self.enemy_state.spawn_time = current_time

    def update(self, dt):
        if self.game_over:
            return
        
        current_time = pygame.time.get_ticks()

        if (
            self.enemy_state.count < self.wave_state.max_enemy_count
            and self.wave_state.active
        ):
            if current_time - self.enemy_state.spawn_time >= self.enemy_state.SPAWN_DELAY:
                self.spawn_enemy()
                self.enemy_state.spawn_time = current_time

        for enemy in self.enemy_state.enemies:
            enemy.update(dt)
            if enemy.reached_end and enemy.is_alive:
                self.health -= enemy.health
                enemy.is_alive = False

        for tower in self.towers:
            tower.find_target(self.enemies)
            self.money += tower.attack(current_time)

        self.enemy_state.enemies = [
            enemy for enemy in self.enemy_state.enemies
            if enemy.is_alive
        ]

        if self.insufficient_funds:
            if (
                current_time - self.insufficient_funds_start_time
                >= self.insufficient_funds_delay
            ):
                self.insufficient_funds = False

        if self.health <= 0:
            self.health = 0
            self.game_over = True
            self.wave_state.cleared = False
            self.enemy_state.enemies = []
            return

        if (
            self.enemy_state.count == self.wave_state.max_enemy_count
            and len(self.enemy_state.enemies) == 0
            and not self.wave_state.cleared
        ):
            self.wave_state.active = False
            self.wave_state.cleared = True
            self.wave_state.cleared_start_time = pygame.time.get_ticks()

        if (
            self.wave_state.cleared
            and current_time - self.wave_state.cleared_start_time
            >= self.wave_state.CLEARED_DELAY
        ):
            self.wave_state.cleared = False
            self.wave_state.next_ready = True

            self.wave_state.round += 1
            self.enemy_state.count = 0
            self.enemy_state.spawn_time = current_time

# __________________________________________________________________

    # def draw_path(self, window):
    #     pygame.draw.lines(
    #         window, "red", False, self.game_map.enemy_path, 1
    #     )

    #     for position in self.game_map.enemy_path: 
    #         x, y = position

    #         pygame.draw.circle(
    #             window, "green", (x,y), 1
    #     )
