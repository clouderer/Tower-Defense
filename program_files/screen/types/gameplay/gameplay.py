from dataclasses import dataclass, field
from typing import ClassVar  # Shared by all classes, like a static attribute.
from pathlib import Path

import pygame

from program_files.screen.types.main_menu import MainMenu

from ....maps.game_map import GameMap
from ....ui.text_object import TextObject
from ....ui.button import Button
from ...screen import Screen
from .enemy.enemy import Enemy
from .tower.tower import Tower
from .tower_slot.tower_slot import TowerSlot
from .tower.bitblaster import BitBlaster
from .tower.proxy_beam import ProxyBeam
from .tower.firewall_pulse import FirewallPulse
from .tower.clock_throttler import ClockThrottler

# """
# [TO DO]:
# EXPECTABLE BEHAVIOR
#     Tower actions
#         Place Tower
#         Upgrade Tower
#         Remove Tower
# """

# Add a display of which wave you had won on

# '''
# During Gameplay when pressing P it opens up the pause menu
# Fix the event handling when introducing new towers
# Figure out how to draw out the healthbar numbers properly
# Font Cleanup
# '''
# [TO DO] Move the GameOver screen into an overlay and implement its functions.

# class GameOverOverlay:
#     GAMEOVER_ASSET_DIR: ClassVar[Path] = (
#         Path(__file__).resolve().parents[4] / "asset_files" / "gameplay"
#     )

#     GAMEOVER_SCREEN_IMG: ClassVar[pygame.Surface] = pygame.image.load(
#         GAMEOVER_ASSET_DIR / "game_over.png"
#     )

#     pass

# class PauseOverlay:
#     PAUSE_ASSET_DIR: ClassVar[Path] = (
#         Path(__file__).resolve().parents[4] / "asset_files" / "gameplay"
#     )

#     PAUSE_SCREEN_IMG: ClassVar[pygame.Surface] = pygame.image.load(
#         PAUSE_ASSET_DIR / "pause.png"
#     )

#     pass


@dataclass
class WaveState:
    """
    Class to manage the state of the waves in the game.
    """
    CLEARED_DELAY: ClassVar[int] = 1200

    round: int = 1
    active: bool = False
    cleared: bool = False
    cleared_start_time: int = None

    next_ready = True

    max_enemy_count: int = 5


@dataclass
class EnemyState:
    """
    Class to manage the state of the enemies in the game.
    """
    SPAWN_DELAY: ClassVar[int] = 3000

    enemies: list[Enemy] = field(default_factory=list)
    count: int = 0
    spawn_time: int = 0


# _____UNUSED_DATACLASSES____
# [TO DO] Decide whether Gameplay needs a tower state.
# [TO DO] Keep tower-slot loading in Gameplay during its redesign.

@dataclass
class TowerState:
    '''
    Class to manage the state of towers in the game.
    '''
    towers: list[Tower] = field(default_factory=list)

# [TO DO] Share static text objects across Gameplay instances where useful.
# [TO DO] Align Gameplay's class variables with its state dataclasses.

# @generated "partially" ChatGPT 5.6 Luna: pygame.get_ticks() timing concept


class Gameplay(Screen):
    INSUFFICIENT_FUNDS_DELAY: ClassVar[int] = 700

    MAX_HEALTH: int = 100
    START_MONEY: int = 300

    GAMEPLAY_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[4] / "asset_files" / "gameplay"

    HEALTHBAR_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "healthbar.png")
    TOWER_SELECTION_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "tower_selection.png")
    BAR_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "bar.png")

    PAUSE_SCREEN_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "pause.png")
    GAMEOVER_SCREEN_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "game_over.png")
    WAVE_CLEARED_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "wave_cleared.png")

    MAIN_MENU_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "main_menu_lit.png")
    MAIN_MENU_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "main_menu_unlit.png")
    REPLAY_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "replay_lit.png")
    REPLAY_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "replay_unlit.png")

    HOME_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "home_lit.png")
    HOME_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "home_unlit.png")
    SETTINGS_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "settings_lit.png")
    SETTINGS_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "settings_unlit.png")
    PAUSE_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "pause_lit.png")
    PAUSE_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "pause_unlit.png")
    RESTART_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "restart_lit.png")
    RESTART_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "restart_unlit.png")

    def __init__(self, app, game_map):
        '''
        Initialize gameplay state, map objects, buttons, and interface text.
        '''
        super().__init__(app)
        self.game_map = game_map

        self.wave_state = WaveState()
        self.enemy_state = EnemyState()

        self.health = self.MAX_HEALTH

        self.money = self.START_MONEY
        self.insufficient_funds = False
        self.insufficient_funds_start_time = 0

        self.towers = []
        self.load_tower_slots()
        self.selected_tower_type = None

        self.paused = False
        self.game_over = False

        self.home_button = Button(
            position=(563, 10),
            lit_img=self.HOME_BUTTON_LIT_IMG,
            unlit_img=self.HOME_BUTTON_UNLIT_IMG,
            action=app.get_main_menu
        )

        self.settings_button = Button(
            position=(532, 10),
            lit_img=self.SETTINGS_BUTTON_LIT_IMG,
            unlit_img=self.SETTINGS_BUTTON_UNLIT_IMG,
            action=app.get_settings
        )

        self.restart_button = Button(
            position=(501, 10),
            lit_img=self.RESTART_BUTTON_LIT_IMG,
            unlit_img=self.RESTART_BUTTON_UNLIT_IMG,
            action=lambda: self.app.change_screen(
                Gameplay(self.app, self.game_map))
        )

        self.pause_button = Button(
            position=(471, 10),
            lit_img=self.PAUSE_BUTTON_LIT_IMG,
            unlit_img=self.PAUSE_BUTTON_UNLIT_IMG,
            action=self.toggle_pause
        )

        self.over_restart_button = Button(
            position=(207, 207),
            lit_img=self.REPLAY_LIT_IMG,
            unlit_img=self.REPLAY_UNLIT_IMG,
            action=lambda: self.app.change_screen(
                Gameplay(self.app, self.game_map))
        )

        self.over_main_menu_button = Button(
            position=(207, 256),
            lit_img=self.MAIN_MENU_LIT_IMG,
            unlit_img=self.MAIN_MENU_UNLIT_IMG,
            action=self.app.get_main_menu
        )

        # Drawable Text Objects
        self.wave_ready_text = TextObject(
            text="PRESS [SPACE] TO START WAVE " + str(self.wave_state.round),
            color="#cffff8",
            position=(300, 338),
            font_size=13
        )

        self.money_text = TextObject(
            text=str(self.money),
            color="#9feef8",
            anchor="midright",
            position=(170, 30),
            font_size=12,
        )

        self.insufficient_funds_text = TextObject(
            text="INSUFFICIENT FUNDS",
            color="Red",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

        self.selected_tower_type_text = TextObject(
            text=(
                "SELECTED: " + self.selected_tower_type.NAME
                if self.selected_tower_type else ""
            ),
            color="White",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

        self.healthbar_text = TextObject(
            text=str(self.health) + "%",
            color="#9feef8",
            anchor="midright",
            position=(70, 30),
            font_size=12,
        )
    # ____GAMEPLAY_LOADING_METHODS____

    def spawn_enemy(self):
        '''
        Create an enemy on the map's route and increment the wave spawn count.
        '''
        self.enemy_state.enemies.append(
            Enemy(self.game_map.enemy_path)
        )
        self.enemy_state.count += 1

    def load_tower_slots(self):
        '''
        Create tower slots at the positions defined by the selected map.
        '''
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    # ____BUTTON_ACTIONS____
    def toggle_pause(self):
        '''
        Toggle pause state while preserving timers across the paused interval.
        '''
        now = pygame.time.get_ticks()

        if not self.paused:
            self.paused = True
            self.pause_start_time = now
            return

        paused_duration = now - self.pause_start_time
        self.enemy_state.spawn_time += paused_duration

        if self.wave_state.cleared_start_time is not None:
            self.wave_state.cleared_start_time += paused_duration

        if self.insufficient_funds:
            self.insufficient_funds_start_time += paused_duration

        for tower in self.towers:
            tower.last_attack_time += paused_duration

        self.paused = False

    # ____EVENT_HANDLING____

    def handle_event(self, event):
        '''
        Handle button input, tower placement, and wave start.
        '''
        if (self.paused):
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
            ):
                self.toggle_pause()
            return

        if self.game_over:
            self.over_main_menu_button.handle_event(event)
            self.over_restart_button.handle_event(event)
            return

        self.pause_button.handle_event(event)
        if self.paused:
            return

        self.restart_button.handle_event(event)
        self.home_button.handle_event(event)
        self.settings_button.handle_event(event)

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
                if self.money >= FirewallPulse.COST:
                    self.set_sufficient(FirewallPulse)
                else:
                    self.set_insufficient()
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                if self.money >= BitBlaster.COST:
                    self.set_sufficient(BitBlaster)
                else:
                    self.set_insufficient()
            elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                if self.money >= ProxyBeam.COST:
                    self.set_sufficient(ProxyBeam)
                else:
                    self.set_insufficient()
            elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                if self.money >= ClockThrottler.COST:
                    self.set_sufficient(ClockThrottler)
                else:
                    self.set_insufficient()

            elif event.key == pygame.K_q:
                self.cancel_tower_placement()
            elif event.key == pygame.K_p:
                pass  # [TO DO] Pause
            elif event.key == pygame.K_SPACE and self.wave_state.next_ready:
                self.wave_state.active = True
                self.wave_state.next_ready = False
                self.enemy_state.spawn_time = pygame.time.get_ticks()

    def set_insufficient(self):
        '''
        Show the insufficient-funds message and start its display timer.
        '''
        self.insufficient_funds = True
        self.insufficient_funds_start_time = pygame.time.get_ticks()

    def set_sufficient(self, tower_type):
        '''
        Clear the funds warning and select a tower type for placement.
        '''
        self.insufficient_funds = False
        self.selected_tower_type = tower_type

    def cancel_tower_placement(self):
        '''
        Cancel the tower selection and clear slot selection and hover states.
        '''
        self.selected_tower_type = None

        for slot in self.tower_slots:
            slot.selected = slot.hovering = False

# ____DRAW_METHOD____

    def draw(self, window):
        """
        Draw the map, gameplay objects, interface, and any active overlay.
        """
        window.blit(self.game_map.image, (0, 0))

        self.draw_tower_slots(window)
        self.draw_towers(window)
        self.draw_enemies(window)

        self.draw_health_power(window)

        self.home_button.draw(window)
        self.settings_button.draw(window)
        self.pause_button.draw(window)
        self.restart_button.draw(window)

        window.blit(self.TOWER_SELECTION_IMG, (445, 295))

        if self.insufficient_funds and not self.wave_state.cleared:
            self.insufficient_funds_text.draw(window)

        if (
            self.selected_tower_type is not None
            and not self.wave_state.cleared
        ):
            self.draw_selected_type(window)

        if self.paused:
            window.blit(self.PAUSE_SCREEN_IMG, (0, 0))
        elif self.game_over:
            self.draw_game_over(window)
        elif self.wave_state.cleared:
            self.draw_wave_cleared(window)
        elif self.wave_state.next_ready:
            self.draw_wave_ready(window)

    # ____DRAW_HELPER_METHODS____
    def draw_tower_slots(self, window):
        '''
        Draw all tower slots.
        '''
        for slot in self.tower_slots:
            slot.draw(window)

    def draw_enemies(self, window):
        '''
        Draw enemies that have not reached the end of the route.
        '''
        for enemy in self.enemy_state.enemies:
            if not enemy.reached_end:
                enemy.draw(window)

    def draw_towers(self, window):
        '''
        Draw all placed towers.
        '''
        for tower in self.towers:
            tower.draw(window)

    def draw_wave_ready(self, window):
        '''
        Draw the prompt to begin the next wave.
        '''
        window.blit(self.BAR_IMG, (0, 0))
        self.wave_ready_text.text = "Press [SPACE] to start WAVE " + str(
            self.wave_state.round)
        self.wave_ready_text.draw(window)

    def draw_game_over(self, window):
        '''
        Draw the game-over screen and its menu and replay buttons.
        '''
        window.blit(self.GAMEOVER_SCREEN_IMG, (0, 0))
        self.over_main_menu_button.draw(window)
        self.over_restart_button.draw(window)

    def draw_wave_cleared(self, window):
        '''
        Draw the wave-cleared message.
        '''
        window.blit(self.WAVE_CLEARED_IMG, (0, 20))

    def draw_selected_type(self, window):
        '''
        Draw the name of the tower type selected for placement.
        '''
        self.selected_tower_type_text.text = (
            "SELECTED: " + self.selected_tower_type.NAME
        )
        self.selected_tower_type_text.draw(window)

    def draw_health_power(self, window):
        '''
        Draw the health bar and refresh the displayed money and health values.
        '''
        window.blit(self.HEALTHBAR_IMG, (10, 15))

        self.money_text.text = str(self.money)
        self.money_text.draw(window)

        self.healthbar_text.text = str(self.health) + "%"
        self.healthbar_text.draw(window)

# ____UPDATE____
    def update(self, dt):
        '''
        Advance gameplay timers, enemies, towers, and wave state for one frame.
        '''
        if self.game_over or self.paused:
            return

        current_time = pygame.time.get_ticks()

        self.update_enemies(current_time, dt)
        self.update_towers(dt)
        self.update_insufficient_funds(current_time)

        if self.health <= 0:
            self.set_game_over()
            return

        if (
            self.enemy_state.count == self.wave_state.max_enemy_count
            and len(self.enemy_state.enemies) == 0
            and not self.wave_state.cleared
        ):
            self.set_wave_cleared(current_time)

        if (
            self.wave_state.cleared
            and current_time - self.wave_state.cleared_start_time
            >= self.wave_state.CLEARED_DELAY
        ):
            self.set_next_wave_ready(current_time)

    def update_enemies(self, current_time, dt):
        '''
        Spawn and move enemies, resolve attacks, and remove defeated enemies.
        '''
        if (
            self.enemy_state.count < self.wave_state.max_enemy_count
            and self.wave_state.active
        ):
            if (
                current_time - self.enemy_state.spawn_time
                >= self.enemy_state.SPAWN_DELAY
            ):
                self.spawn_enemy()
                self.enemy_state.spawn_time = current_time

        for enemy in self.enemy_state.enemies:
            enemy.update(dt)
            if enemy.reached_end and enemy.is_alive:
                self.health -= enemy.health
                enemy.is_alive = False

        for tower in self.towers:
            tower.find_target(self.enemy_state.enemies)
            self.money += tower.attack(current_time)

        self.enemy_state.enemies = [
            enemy for enemy in self.enemy_state.enemies
            if enemy.is_alive
        ]

    def update_towers(self, dt):
        '''
        Update each placed tower.
        '''
        for tower in self.towers:
            tower.update(dt)

    def update_insufficient_funds(self, current_time):
        '''
        Hide the insufficient-funds message after its display delay.
        '''
        if self.insufficient_funds:
            if (
                current_time - self.insufficient_funds_start_time
                >= self.INSUFFICIENT_FUNDS_DELAY
            ):
                self.insufficient_funds = False
                self.insufficient_funds_start_time = None

    def set_game_over(self):
        '''
        Enter the game-over state and remove remaining enemies.
        '''
        self.health = 0
        self.game_over = True
        self.wave_state.cleared = False
        self.enemy_state.enemies = []

    def set_wave_cleared(self, current_time):
        '''
        Mark the current wave as cleared and record when the clear began.
        '''
        self.wave_state.active = False
        self.wave_state.cleared = True
        self.wave_state.cleared_start_time = current_time

    def set_next_wave_ready(self, current_time):
        '''
        Prepare the next wave by updating limits and resetting spawn state.
        '''
        self.wave_state.cleared = False
        self.wave_state.next_ready = True

        self.wave_state.round += 1
        self.wave_state.max_enemy_count += 5

        self.enemy_state.count = 0
        self.enemy_state.spawn_time = current_time
    # [TO DO] Implement these Gameplay update helpers:
    # update_health(),
    # update_towers(current_time), update_selected_tower_type(),
    # update_tower_slots(), update_money().

    def draw_path(self, window):
        '''
        Draw the enemy route and mark each waypoint.
        '''
        pygame.draw.lines(
            window, "red", False, self.game_map.enemy_path, 1
        )

        for position in self.game_map.enemy_path:
            x, y = position

            pygame.draw.circle(
                window, "green", (x, y), 1
            )

    # Outdated method of Gameplay used in the past for enemy updating

    def update_enemy_spawn(self, current_time):
        '''
        Spawn an enemy when the active wave's spawn delay has elapsed.
        '''
        if not self.wave_state.active:
            return

        if self.enemy_state.count >= self.wave_state.max_enemy_count:
            return

        if (
            current_time - self.enemy_state.spawn_time
            < self.enemy_state.SPAWN_DELAY
        ):
            return

        self.spawn_enemy()
        self.enemy_state.spawn_time = current_time
