"""Handle waves, enemies, towers, and the gameplay interface."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, Optional

import pygame

from ....maps.game_map import GameMap
from ....ui.button import Button
from ....ui.text_object import TextObject
from ...screen import Screen
from .enemy.enemy import Enemy
from .enemy.leaked_file import LeakedFile
from .enemy.trojan_file import TrojanFile
from .enemy.wave_config import get_wave_spawns
from .tower.bitblaster import BitBlaster
from .tower.clock_throttler import ClockThrottler
from .tower.firewall_pulse import FirewallPulse
from .tower.proxy_beam import ProxyBeam
from .tower.tower import Tower
from .tower_slot.tower_slot import TowerSlot


@dataclass
class WaveState:
    """Store the current wave number, state, and clear message timer."""
    CLEARED_DELAY: ClassVar[int] = 1200
    MAX_WAVES: ClassVar[int] = 25

    round: int = 1

    active: bool = False
    cleared: bool = False
    cleared_start_time: Optional[int] = None
    next_ready: bool = True
    won: bool = False

    # Holds the set of waves, which are currently active. 
    active_waves: set[int] = field(default_factory=set)
    # Holds the set of waves which were rewarded.
    rewarded_waves: set[int] = field(default_factory=set)


@dataclass(frozen=True)
class EnemySpawn:
    """Keep a queued enemy's type, level, and wave number together."""
    enemy_type: type[Enemy]
    level: int
    wave_number: int


@dataclass
class EnemyState:
    """Store active enemies and the enemies waiting to spawn."""
    enemies: list[Enemy] = field(default_factory=list)
    spawn_queue: list[EnemySpawn] = field(default_factory=list)
    count: int = 0
    spawn_time: int = 0
    wave_spawn_times: dict[int, int] = field(default_factory=dict)


# @generated "partially" ChatGPT 5.6 Luna: timing concept
class Gameplay(Screen):
    """
    Manage tower actions, enemy waves, and the player's health and
    money.
    """

    INSUFFICIENT_FUNDS_DELAY: ClassVar[int] = 700
    ENEMY_SPAWN_INTERVAL: ClassVar[int] = 1200
    WAVE_CLEAR_REWARD_BASE: ClassVar[int] = 50
    WAVE_CLEAR_REWARD_PER_WAVE: ClassVar[int] = 21

    MAX_HEALTH: ClassVar[int] = 100
    START_MONEY: ClassVar[int] = 100

    TOWER_SELECTION: ClassVar[list[Tower]] = [
        FirewallPulse, BitBlaster, ProxyBeam, ClockThrottler
    ]
    TOWER_SELECTION_POS: ClassVar[list[tuple[int, int]]] = [
        (451, 301), (487, 301), (523, 301), (559, 301)
    ]

    GAMEPLAY_ASSET_DIR: ClassVar[Path] = Path(
        __file__).resolve().parents[4] / "asset_files" / "gameplay"

    HEALTHBAR_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "healthbar.png")
    
    TOWER_SELECTION_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "tower_selection.png")
    SELECTION_OVERLAY_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "selection_overlay.png")
    SELECTED_OVERLAY_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "selected_overlay.png")
    
    START_WAVE_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "bar.png")
    SKIP_WAVE_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "skip_wave.png")

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

    SELL_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "sidebar" / "sell_hover.png")
    SELL_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "sidebar" / "sell_normal.png")
    UPGRADE_BUTTON_LIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "sidebar" / "upgrade_hover.png")
    UPGRADE_BUTTON_UNLIT_IMG: ClassVar[pygame.Surface] = pygame.image.load(
        GAMEPLAY_ASSET_DIR / "sidebar" / "upgrade_normal.png")

    HUD_TEXT_COLOR: ClassVar[pygame.Color] = "#9feef8"
    PROMPT_TEXT_COLOR: ClassVar[pygame.Color] = "#cffff8"
    AFFORDABLE_COLOR: ClassVar[pygame.Color] = HUD_TEXT_COLOR
    UNAFFORDABLE_COLOR: ClassVar[pygame.Color] = "#636363"
    SELECTED_COLOR: ClassVar[pygame.Color] = "#9acd32"

    def __init__(self, app: App, game_map: GameMap) -> None:
        """
        Initialize gameplay state, map objects, buttons, and interface
        text.
        """
        super().__init__(app)
        self.game_map = game_map

        self.wave_state = WaveState()
        self.enemy_state = EnemyState()

        self.wave_ready_rect = self.START_WAVE_IMG.get_rect(
            midbottom=(self.game_map.width // 2, self.game_map.height),
        )

        self.skip_wave_rect = self.SKIP_WAVE_IMG.get_rect(
            midtop=(self.game_map.width // 2 + 13, 0),
        )

        self.health = self.MAX_HEALTH

        self.money = self.START_MONEY
        self.insufficient_funds = False
        self.insufficient_funds_start_time = 0

        self.towers: list[Tower] = []
        self.load_tower_slots()
        self.selected_tower_type = None
        self.tower_selection_rects = self.make_selection_rects()

        self.placement_preview = None
        self.placement_preview_slot = None
        self.placement_preview_type = None

        self.paused = False
        self.resume_after_overlay = False
        self.game_over = False

        self.sidebar_tower = None
        self.sidebar_tower_idx = None

        # Create the buttons used during gameplay and after a loss.
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

        self.sell_button = Button(
            position=(517, 307),
            lit_img=self.SELL_BUTTON_LIT_IMG,
            unlit_img=self.SELL_BUTTON_UNLIT_IMG,
            action=self.sell_tower
        )

        self.upgrade_button = Button(
            position=(383, 307),
            lit_img=self.UPGRADE_BUTTON_LIT_IMG,
            unlit_img=self.UPGRADE_BUTTON_UNLIT_IMG,
            action=self.upgrade_tower
        )

        # Create the labels for the wave, money, health, and tower
        # prices.
        self.wave_ready_text = TextObject(
            text=(
                "CLICK OR [SPACE] TO START WAVE " + str(self.wave_state.round)
            ),
            color=self.PROMPT_TEXT_COLOR,
            position=self.wave_ready_rect.center,
            font_size=10,
        )

        self.skip_wave_text = TextObject(
            text="CLICK OR PRESS [S] TO SKIP",
            color=self.PROMPT_TEXT_COLOR,
            position=self.skip_wave_rect.center,
            font_size=10,
        )

        self.victory_text = TextObject(
            text="ALL 25 WAVES CLEARED",
            color=self.PROMPT_TEXT_COLOR,
            position=(300, 220),
            font_size=12,
        )

        self.money_text = TextObject(
            text=str(self.money),
            color=self.HUD_TEXT_COLOR,
            anchor="midright",
            position=(170, 28),
            font_size=12,
        )

        self.insufficient_funds_text = TextObject(
            text="INSUFFICIENT FUNDS",
            color="Red",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

        self.quit_placing_text = TextObject(
            text="PRESS [Q] TO QUIT PLACING",
            color="Red",
            anchor="bottomleft",
            position=(10, 340),
            font_size=10,
        )

        self.healthbar_text = TextObject(
            text=str(self.health) + "%",
            color=self.HUD_TEXT_COLOR,
            anchor="midright",
            position=(78, 28),
            font_size=12,
        )

        self.tower_price_text = [
            TextObject(
                text=str(FirewallPulse.COST),
                color=self.HUD_TEXT_COLOR,
                position=(474, 340),
                font_size=8,
            ),

            TextObject(
                text=str(BitBlaster.COST),
                color=self.HUD_TEXT_COLOR,
                position=(510, 340),
                font_size=8,
            ),

            TextObject(
                text=str(ProxyBeam.COST),
                color=self.HUD_TEXT_COLOR,
                position=(546, 340),
                font_size=8,
            ),

            TextObject(
                text=str(ClockThrottler.COST),
                color=self.HUD_TEXT_COLOR,
                position=(582, 340),
                font_size=8,
            ),
        ]

    def spawn_enemy(self, wave_number:int | None = None) -> None:
        """
        Spawn the next queued enemy belonging to the requested wave.
        """
        if not self.enemy_state.spawn_queue:
            return

        if wave_number is None:
            wave_number = self.wave_state.round
        index = next(
            (index for index, spawn in enumerate(self.enemy_state.spawn_queue)
             if spawn.wave_number == wave_number),
            None,
        )
        if index is None:
            return

        spawn = self.enemy_state.spawn_queue.pop(index)
        enemy = spawn.enemy_type(self.game_map.enemy_path, level=spawn.level)
        enemy.wave_number = spawn.wave_number
        self.enemy_state.enemies.append(enemy)
        self.enemy_state.count += 1

    def start_wave(self) -> None:
        """Start the ready wave without removing earlier enemies."""
        if (
            not self.wave_state.next_ready or self.paused
            or self.game_over or self.wave_state.won
        ):
            return

        wave_number = self.wave_state.round
        self.enemy_state.spawn_queue.extend(
            EnemySpawn(enemy_type, level, wave_number)
            for enemy_type, level in get_wave_spawns(wave_number)
        )
        self.enemy_state.count = 0
        self.wave_state.active = True
        self.wave_state.active_waves.add(wave_number)
        self.wave_state.next_ready = False
        self.wave_state.cleared = False
        self.wave_state.cleared_start_time = None

        now = pygame.time.get_ticks()
        self.enemy_state.spawn_time = now - self.ENEMY_SPAWN_INTERVAL
        self.enemy_state.wave_spawn_times[wave_number] = (
            self.enemy_state.spawn_time
        )

    @property
    def can_skip_wave(self) -> bool:
        """Allow skipping an active wave while gameplay is running."""
        return (
            self.wave_state.active
            and not self.wave_state.next_ready
            and not self.wave_state.cleared
            and self.wave_state.round < self.wave_state.MAX_WAVES
            and not self.paused 
            and not self.game_over
            and not self.wave_state.won
        )

    def skip_wave(self) -> None:
        """Start the next wave while earlier waves continue normally."""
        if not self.can_skip_wave:
            return
        self.reward_wave(self.wave_state.round)
        self.wave_state.round += 1
        self.wave_state.next_ready = True
        self.start_wave()

    def load_tower_slots(self) -> None:
        """
        Create tower slots at the positions defined by the selected map.
        """
        self.tower_slots = [
            TowerSlot(position)
            for position in self.game_map.tower_positions]

    def make_selection_rects(self) -> list[pygame.Rect]:
        """
        Create the clickable areas for the tower selection buttons.
        """
        rects = [
            pygame.Rect(rect_pos, (28, 28))
            for rect_pos in self.TOWER_SELECTION_POS
        ]

        return rects

    def on_suspend(self) -> None:
        """Pause gameplay while another screen is open above it."""
        self.resume_after_overlay = not self.paused
        if self.resume_after_overlay:
            self.toggle_pause()

    def on_resume(self) -> None:
        """
        Resume gameplay and adjust timers after closing another screen.
        """
        if self.resume_after_overlay:
            self.toggle_pause()
            self.resume_after_overlay = False

    def toggle_pause(self) -> None:
        """
        Toggle pause state while preserving timers across the paused
        interval.
        """
        now = pygame.time.get_ticks()

        if not self.paused:
            self.paused = True
            self.pause_start_time = now
            return

        paused_duration = now - self.pause_start_time
        self.enemy_state.spawn_time += paused_duration

        # Because of the skippable waves, we also need to add the 
        # paused duration to the times of each started waves.
        for wave_number in self.enemy_state.wave_spawn_times:
            self.enemy_state.wave_spawn_times[wave_number] += paused_duration

        if self.wave_state.cleared_start_time is not None:
            self.wave_state.cleared_start_time += paused_duration

        if self.insufficient_funds:
            self.insufficient_funds_start_time += paused_duration

        for tower in self.towers:
            tower.last_attack_time += paused_duration

        self.paused = False

    def sell_tower(self) -> None:
        """Sell the selected tower and free its slot."""
        tower = self.sidebar_tower
        index = self.sidebar_tower_idx
        if (
            tower is None
            or index is None
            or index < 0
            or index >= len(self.towers)
            or self.towers[index] is not tower
        ):
            return

        self.money += int(round(tower.total_cost * 1))
        tower.tower_slot.occupied = False
        tower.tower_slot.selected = False
        del self.towers[index]
        self.sidebar_tower = None
        self.sidebar_tower_idx = None

    def upgrade_tower(self) -> None:
        """
        Upgrade the selected tower when the player has enough money.
        """
        tower = self.sidebar_tower
        if tower is None or not tower.can_upgrade:
            return

        cost = tower.next_upgrade_cost
        if self.money < cost:
            self.set_insufficient()
            return

        if tower.upgrade():
            self.money -= cost
            tower.total_cost += cost
            self.insufficient_funds = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle button input, tower placement, and wave start."""
        if self.paused:
            if (
                (event.type == pygame.KEYDOWN and event.key == pygame.K_p)
                or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
            ):
                self.toggle_pause()
            return

        if self.game_over:
            self.over_main_menu_button.handle_event(event)
            self.over_restart_button.handle_event(event)
            return
        if self.wave_state.won:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1): 
                self.app.get_main_menu()
            return
        if self.pause_button.handle_event(event):
            return

        if (
            (event.type == pygame.KEYDOWN and event.key == pygame.K_s)
            or
            (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            and self.can_skip_wave
            and self.skip_wave_rect.collidepoint(event.pos))
        ):
            self.skip_wave()
            return

        if self.sidebar_tower is not None:
            if (
                self.sell_button.handle_event(event)
                or self.upgrade_button.handle_event(event)
            ):
                return
        else:
            for button in (
                self.restart_button, self.home_button, self.settings_button
            ):
                if button.handle_event(event):
                    return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if (
                self.wave_state.next_ready
                and self.wave_ready_rect.collidepoint(event.pos)
            ):
                self.start_wave()
                return

            if self.sidebar_tower is not None:
                self.sidebar_tower = self.sidebar_tower_idx = None
            if self.selected_tower_type is not None:

                clicked_slot = None

                for slot in self.tower_slots:
                    if slot.rect.collidepoint(event.pos):
                        clicked_slot = slot
                        slot.selected = True
                        break

                if clicked_slot is not None and not clicked_slot.occupied:
                    if self.money < self.selected_tower_type.COST:
                        self.set_insufficient()
                        self.cancel_tower_placement()
                        return
                    clicked_slot.occupied = True

                    self.money -= self.selected_tower_type.COST
                    self.towers.append(self.selected_tower_type(clicked_slot))
                    self.selected_tower_type = None

                    self.cancel_tower_placement()
                else:
                    self.cancel_tower_placement()

            elif self.selected_tower_type is None:
                for i in range(len(self.tower_selection_rects)):
                    if self.tower_selection_rects[i].collidepoint(event.pos):
                        if self.money >= self.TOWER_SELECTION[i].COST:
                            self.set_sufficient(self.TOWER_SELECTION[i])
                        else:
                            self.set_insufficient()

                for i, tower in enumerate(self.towers):
                    if tower.rect.collidepoint(event.pos):
                        self.sidebar_tower = tower
                        self.sidebar_tower_idx = i
                        break

        if (
            event.type == pygame.MOUSEMOTION
            and self.selected_tower_type is not None
        ):
            hovered_slot = None
            for slot in self.tower_slots:
                slot.hovering = slot.rect.collidepoint(event.pos)
                if slot.hovering:
                    hovered_slot = slot

            if hovered_slot is None:
                self.placement_preview = None
                self.placement_preview_slot = None
                self.placement_preview_type = None
            elif (
                self.placement_preview_slot is not hovered_slot
                or self.placement_preview_type is not self.selected_tower_type
            ):
                self.placement_preview = self.selected_tower_type(
                    hovered_slot
                )
                self.placement_preview_slot = hovered_slot
                self.placement_preview_type = self.selected_tower_type

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
                self.toggle_pause()
            elif event.key == pygame.K_SPACE and self.wave_state.next_ready:
                self.start_wave()

    def set_insufficient(self) -> None:
        """
        Show the insufficient-funds message and start its display timer.
        """
        self.insufficient_funds = True
        self.insufficient_funds_start_time = pygame.time.get_ticks()

    def set_sufficient(self, tower_type: type[Tower]) -> None:
        """
        Clear the funds warning and select a tower type for placement.
        """
        self.insufficient_funds = False
        self.selected_tower_type = tower_type
        self.placement_preview = None
        self.placement_preview_slot = None
        self.placement_preview_type = None

    def cancel_tower_placement(self) -> None:
        """
        Cancel the tower selection and clear slot selection and hover
        states.
        """
        self.selected_tower_type = None
        self.placement_preview = None
        self.placement_preview_slot = None
        self.placement_preview_type = None

        for slot in self.tower_slots:
            slot.selected = slot.hovering = False

    def draw(self, window: pygame.Surface) -> None:
        """
        Draw the map, gameplay objects, interface, and any active
        overlay.
        """
        window.blit(self.game_map.image, (0, 0))

        self.draw_tower_slots(window)
        self.draw_placement_preview(window)
        self.draw_towers(window)
        self.draw_enemies(window)

        self.draw_health_power(window)

        self.home_button.draw(window)
        self.settings_button.draw(window)
        self.pause_button.draw(window)
        self.restart_button.draw(window)

        window.blit(self.TOWER_SELECTION_IMG, (445, 295))
        for i in range(len(self.TOWER_SELECTION)):
            self.draw_tower_cost_selection(
                self.TOWER_SELECTION[i],
                self.tower_price_text[i],
                self.TOWER_SELECTION_POS[i],
                window,
            )

        if self.insufficient_funds and not self.wave_state.cleared:
            self.insufficient_funds_text.draw(window)
        elif (
            self.selected_tower_type is not None
            and not self.wave_state.cleared
        ):
            self.draw_selected_type(window)

        if self.paused:
            window.blit(self.PAUSE_SCREEN_IMG, (0, 0))
        elif self.game_over:
            self.draw_game_over(window)
        elif self.wave_state.won:
            self.draw_wave_cleared(window)
            self.victory_text.draw(window)
        elif (self.sidebar_tower is not None):
            self.draw_sidebar(window)
        elif self.wave_state.cleared:
            self.draw_wave_cleared(window)
        elif self.wave_state.next_ready:
            self.draw_wave_ready(window)

        if (self.can_skip_wave and self.sidebar_tower is None):
            self.draw_skip_wave(window)
    def draw_sidebar(self, window: pygame.Surface) -> None:
        """
        Darken the map and draw the selected tower and its sidebar.
        """
        black_overlay = pygame.Surface((600, 350))
        black_overlay.fill((0, 0, 0))
        black_overlay.set_alpha(90)
        window.blit(black_overlay, (0, 0))

        self.sidebar_tower.draw_underlay(window)
        self.sidebar_tower.draw(window)
        self.sidebar_tower.draw_sidebar(window)
        self.sell_button.draw(window)
        self.upgrade_button.draw(window)

    def draw_tower_cost_selection(
        self,
        tower_type: type[Tower],
        text: TextObject,
        pos: tuple[int, int],
        window: pygame.Surface,
    ) -> None:
        """
        Show the tower price and mark towers the player cannot afford.
        """
        if tower_type.COST <= self.money:
            text.color = self.AFFORDABLE_COLOR
        else:
            text.color = self.UNAFFORDABLE_COLOR
            window.blit(self.SELECTION_OVERLAY_IMG, pos)
        text.draw(window)

    def draw_tower_slots(self, window: pygame.Surface) -> None:
        """Draw all tower slots."""
        for slot in self.tower_slots:
            slot.draw(window)

    def draw_enemies(self, window: pygame.Surface) -> None:
        """Draw enemies that have not reached the end of the route."""
        for enemy in self.enemy_state.enemies:
            if not enemy.reached_end:
                enemy.draw(window)

    def draw_towers(self, window: pygame.Surface) -> None:
        """Draw all placed towers."""
        for tower in self.towers:
            tower.draw(window)

    def draw_placement_preview(self, window: pygame.Surface) -> None:
        """Draw the hovered tower and its range at low opacity."""
        if (self.selected_tower_type is None or
            self.placement_preview is None
        ):
            return

        if self.placement_preview.underlay_sprite is not None:
            range_image = self.placement_preview.underlay_sprite.image.copy()
            range_image.set_alpha(110)
            window.blit(
                range_image, self.placement_preview.underlay_sprite.rect
            )

        tower_image = self.placement_preview.image.copy()
        tower_image.set_alpha(110)
        window.blit(tower_image, self.placement_preview.rect)

    def draw_wave_ready(self, window: pygame.Surface) -> None:
        """Draw the prompt to begin the next wave."""
        window.blit(self.START_WAVE_IMG, self.wave_ready_rect)
        self.wave_ready_text.text = (
            "CLICK OR [SPACE] TO START WAVE " + str(self.wave_state.round)
        )
        self.wave_ready_text.draw(window)

    def draw_skip_wave(self, window: pygame.Surface) -> None:
        """Draw the skip prompt at the top center of the map."""
        window.blit(self.SKIP_WAVE_IMG, self.skip_wave_rect)
        self.skip_wave_text.draw(window)

    def draw_game_over(self, window: pygame.Surface) -> None:
        """Draw the game-over screen and its menu and replay buttons."""
        window.blit(self.GAMEOVER_SCREEN_IMG, (0, 0))
        self.over_main_menu_button.draw(window)
        self.over_restart_button.draw(window)

    def draw_wave_cleared(self, window: pygame.Surface) -> None:
        """Draw the wave-cleared message."""
        window.blit(self.WAVE_CLEARED_IMG, (0, 20))

    def draw_selected_type(self, window: pygame.Surface) -> None:
        """
        Draw the selection marker and the prompt to cancel tower
        placement.
        """

        idx = self.TOWER_SELECTION.index(self.selected_tower_type)
        window.blit(self.SELECTED_OVERLAY_IMG, self.TOWER_SELECTION_POS[idx])

        self.quit_placing_text.draw(window)

    def draw_health_power(self, window: pygame.Surface) -> None:
        """
        Draw the health bar and refresh the displayed money and health
        values.
        """
        window.blit(self.HEALTHBAR_IMG, (10, 15))

        self.money_text.text = str(self.money)
        self.money_text.draw(window)

        self.healthbar_text.text = str(self.health) + "%"
        self.healthbar_text.draw(window)

    def update(self, dt: float) -> None:
        """
        Advance gameplay timers, enemies, towers, and wave state for one
        frame.
        """
        if self.game_over or self.paused or self.wave_state.won:
            return

        current_time = pygame.time.get_ticks()

        self.update_enemies(current_time, dt)
        self.update_towers(dt)
        self.update_insufficient_funds(current_time)

        if self.health <= 0:
            self.set_game_over()
            return

        self.update_wave_rewards()

        if (
            self.wave_state.active
            and not self.enemy_state.spawn_queue
            and not self.enemy_state.enemies
            and not self.wave_state.cleared
        ):
            self.set_wave_cleared(current_time)

        if (
            self.wave_state.cleared
            and current_time - self.wave_state.cleared_start_time
            >= self.wave_state.CLEARED_DELAY
        ):
            self.set_next_wave_ready(current_time)

    def update_enemies(self, current_time: int, dt: float) -> None:
        """
        Spawn and move enemies, resolve attacks, and remove defeated
        enemies.
        """
        self.update_enemy_spawn(current_time)

        for enemy in list(self.enemy_state.enemies):
            enemy.update(dt)
            wave_number = getattr(enemy, "wave_number", self.wave_state.round)

            if isinstance(enemy, TrojanFile):
                spawnling_path = enemy.consume_spawnling()
                if spawnling_path:
                    spawnling = LeakedFile(spawnling_path, level=enemy.level)
                    spawnling.wave_number = wave_number
                    enemy.register_spawnling(spawnling)
                    self.enemy_state.enemies.append(spawnling)

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

    def update_towers(self, dt: float) -> None:
        """Update each placed tower."""
        for tower in self.towers:
            tower.update(dt)

    def update_insufficient_funds(self, current_time: int) -> None:
        """
        Hide the insufficient-funds message after its display delay.
        """
        if self.insufficient_funds:
            if (
                current_time - self.insufficient_funds_start_time
                >= self.INSUFFICIENT_FUNDS_DELAY
            ):
                self.insufficient_funds = False
                self.insufficient_funds_start_time = None

    def set_game_over(self) -> None:
        """Enter the game-over state and remove remaining enemies."""
        self.health = 0
        self.game_over = True
        self.wave_state.cleared = False
        self.enemy_state.enemies = []

    def reward_wave(self, wave_number: int) -> None:
        """Pay once when the wave can be skipped or clears."""
        if wave_number in self.wave_state.rewarded_waves:
            return
        self.money += (
            self.WAVE_CLEAR_REWARD_BASE
            + wave_number * self.WAVE_CLEAR_REWARD_PER_WAVE
        )
        self.wave_state.rewarded_waves.add(wave_number)

    def update_wave_rewards(self) -> None:
        """Pay completed waves and check queued and living enemies."""
        unfinished_waves = {
            spawn.wave_number for spawn in self.enemy_state.spawn_queue
        }
        unfinished_waves.update(
            getattr(enemy, "wave_number", self.wave_state.round)
            for enemy in self.enemy_state.enemies if enemy.is_alive
        )
        completed_waves = self.wave_state.active_waves - unfinished_waves
        for wave_number in sorted(completed_waves):
            self.reward_wave(wave_number)
            self.wave_state.active_waves.remove(wave_number)
            self.enemy_state.wave_spawn_times.pop(wave_number, None)

    def set_wave_cleared(self, current_time: int) -> None:
        """
        Mark the wave as cleared, give its reward, and start the clear
        timer.
        """
        if not self.wave_state.active:
            return
        self.wave_state.active = False
        self.wave_state.cleared = True
        self.wave_state.cleared_start_time = current_time
        self.reward_wave(self.wave_state.round)

    def set_next_wave_ready(self, current_time: int) -> None:
        """
        Prepare the next wave, or mark victory after the final wave.
        """
        self.wave_state.cleared = False
        self.wave_state.cleared_start_time = None
        self.enemy_state.count = 0
        self.enemy_state.spawn_queue.clear()
        self.enemy_state.wave_spawn_times.clear()
        self.enemy_state.spawn_time = current_time

        if self.wave_state.round >= self.wave_state.MAX_WAVES:
            self.wave_state.active = False
            self.wave_state.next_ready = False
            self.wave_state.won = True
            return

        self.wave_state.next_ready = True
        self.wave_state.round += 1

    def draw_path(self, window: pygame.Surface) -> None:
        """Draw the enemy route and mark each waypoint."""
        pygame.draw.lines(
            window, "red", False, self.game_map.enemy_path, 1
        )

        for position in self.game_map.enemy_path:
            x, y = position

            pygame.draw.circle(
                window, "green", (x, y), 1
            )

    def update_enemy_spawn(self, current_time: int) -> None:
        """
        Keep each started wave spawning at its normal interval.
        """
        if not self.wave_state.active or not self.enemy_state.spawn_queue:
            return

        spawning_waves = dict.fromkeys(
            spawn.wave_number for spawn in self.enemy_state.spawn_queue
        )
        for wave_number in spawning_waves:
            if wave_number == self.wave_state.round:
                spawn_time = self.enemy_state.spawn_time
            else:
                spawn_time = self.enemy_state.wave_spawn_times[wave_number]
            if current_time - spawn_time < self.ENEMY_SPAWN_INTERVAL:
                continue

            self.spawn_enemy(wave_number)
            self.enemy_state.wave_spawn_times[wave_number] = current_time
            if wave_number == self.wave_state.round:
                self.enemy_state.spawn_time = current_time
