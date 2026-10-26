"""Check application startup and gameplay input behavior."""


# @generated fully ChatGPT 6.1 Sol: Tests

import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.tower.firewall_pulse import (
    FirewallPulse,
)
from program_files.screen.types.tutorial import Tutorial
from program_files.ui.text_object import get_font


class ApplicationTests(unittest.TestCase):
    """Check screen changes, tower actions, and wave rewards."""

    @classmethod
    def setUpClass(cls):
        """Initialize Pygame once for the application checks."""
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        """Release cached fonts before closing Pygame."""
        get_font.cache_clear()
        pygame.quit()

    def setUp(self):
        """Create a new app and gameplay screen for each check."""
        self.app = App()
        self.app.get_gameplay(NEON_GRID_MAP)
        self.gameplay = self.app.current_screen

    def add_tower(self):
        """Place a Firewall Pulse in the first tower slot."""
        slot = self.gameplay.tower_slots[0]
        slot.occupied = True
        tower = FirewallPulse(slot)
        self.gameplay.towers.append(tower)
        return tower

    def test_import_does_not_start_game(self):
        """Importing app.py must leave Pygame and the game loop idle."""
        code = (
            "import pygame; import program_files.app; "
            "assert not pygame.get_init()"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_app_module_entry_point_starts_and_exits(self):
        """Start the app module and send a real quit event."""
        code = (
            "import runpy, pygame; from unittest.mock import patch; "
            "events = patch('pygame.event.get', return_value="
            "[pygame.event.Event(pygame.QUIT)]); events.start(); "
            "runpy.run_module('program_files.app', run_name='__main__'); "
            "assert not pygame.get_init()"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_upgrade_button_keeps_sidebar_open(self):
        """Keep the selected tower's sidebar open after an upgrade."""
        tower = self.add_tower()
        self.gameplay.sidebar_tower = tower
        self.gameplay.sidebar_tower_idx = 0
        self.gameplay.money = 1000
        cost = tower.next_upgrade_cost
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=self.gameplay.upgrade_button.rect.center,
        )

        self.gameplay.handle_event(event)

        self.assertEqual(tower.level, 2)
        self.assertEqual(self.gameplay.money, 1000 - cost)
        self.assertIs(self.gameplay.sidebar_tower, tower)

    def test_placement_checks_current_money(self):
        """Reject placement when the player cannot afford the tower."""
        self.gameplay.selected_tower_type = FirewallPulse
        self.gameplay.money = FirewallPulse.COST - 1
        slot = self.gameplay.tower_slots[0]
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=slot.rect.center
        )

        self.gameplay.handle_event(event)

        self.assertEqual(self.gameplay.towers, [])
        self.assertFalse(slot.occupied)
        self.assertEqual(self.gameplay.money, FirewallPulse.COST - 1)
        self.assertTrue(self.gameplay.insufficient_funds)

    def test_pause_key_also_resumes(self):
        """Pressing P twice must pause and then resume the game."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        self.gameplay.handle_event(event)
        self.assertTrue(self.gameplay.paused)
        self.gameplay.handle_event(event)
        self.assertFalse(self.gameplay.paused)

    def test_settings_preserve_gameplay_timers(self):
        """Time in settings must not count toward gameplay cooldowns."""
        tower = self.add_tower()
        tower.last_attack_time = 100
        self.gameplay.enemy_state.spawn_time = 100
        with patch("pygame.time.get_ticks", return_value=1000):
            self.app.get_settings()
        self.assertTrue(self.gameplay.paused)

        with patch("pygame.time.get_ticks", return_value=5000):
            self.app.pop_screen()

        self.assertIs(self.app.current_screen, self.gameplay)
        self.assertFalse(self.gameplay.paused)
        self.assertEqual(tower.last_attack_time, 4100)
        self.assertEqual(self.gameplay.enemy_state.spawn_time, 4100)

    def test_wave_reward_is_paid_once(self):
        """The same completed wave must not give its reward twice."""
        self.gameplay.money = 0
        self.gameplay.wave_state.active = True
        self.gameplay.wave_state.round = 4
        self.gameplay.set_wave_cleared(1000)
        reward = self.gameplay.money
        self.gameplay.set_wave_cleared(2000)
        self.assertEqual(
            reward, self.gameplay.WAVE_CLEAR_REWARD_BASE
            + 4 * self.gameplay.WAVE_CLEAR_REWARD_PER_WAVE,
        )
        self.assertGreater(reward, 0)
        self.assertEqual(self.gameplay.wave_state.rewarded_waves, {4})
        self.assertEqual(self.gameplay.money, reward)

    def test_clicking_wave_banner_starts_the_ready_wave(self):
        """Start the wave from the visible part of the banner."""
        self.assertEqual(
            self.gameplay.wave_ready_rect,
            self.gameplay.START_WAVE_IMG.get_rect(midbottom=(
                self.gameplay.game_map.width // 2,
                self.gameplay.game_map.height,
            )),
        )
        self.assertEqual(
            self.gameplay.wave_ready_rect.width,
            self.gameplay.START_WAVE_IMG.get_width(),
        )
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=self.gameplay.wave_ready_rect.center,
        )

        self.gameplay.handle_event(event)

        self.assertTrue(self.gameplay.wave_state.active)
        self.assertFalse(self.gameplay.wave_state.next_ready)
        self.assertTrue(self.gameplay.enemy_state.spawn_queue)

    def test_outside_and_right_clicks_do_not_start_the_wave(self):
        """Ignore clicks outside the banner and right mouse clicks."""
        banner = self.gameplay.wave_ready_rect
        for button, position in (
            (1, (banner.left - 1, banner.centery)),
            (3, banner.center),
        ):
            with self.subTest(button=button, position=position):
                event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=button, pos=position
                )

                self.gameplay.handle_event(event)

                self.assertFalse(self.gameplay.wave_state.active)
                self.assertTrue(self.gameplay.wave_state.next_ready)
                self.assertEqual(self.gameplay.enemy_state.spawn_queue, [])

    def test_banner_click_does_not_restart_an_active_wave(self):
        """Keep the remaining queue when a wave is already active."""
        self.gameplay.start_wave()
        self.gameplay.spawn_enemy()
        remaining_queue = self.gameplay.enemy_state.spawn_queue
        queue_contents = list(remaining_queue)
        spawn_time = self.gameplay.enemy_state.spawn_time
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=self.gameplay.wave_ready_rect.center,
        )

        self.gameplay.handle_event(event)

        self.assertIs(self.gameplay.enemy_state.spawn_queue, remaining_queue)
        self.assertEqual(remaining_queue, queue_contents)
        self.assertEqual(self.gameplay.enemy_state.count, 1)
        self.assertEqual(self.gameplay.enemy_state.spawn_time, spawn_time)

    def test_banner_click_preserves_tower_placement_without_spending(
        self,
    ):
        """Consume the start click before handling tower placement."""
        self.gameplay.selected_tower_type = FirewallPulse
        slot = self.gameplay.tower_slots[0]
        slot.rect.center = self.gameplay.wave_ready_rect.center
        slot.selected = True
        slot.hovering = True
        money = self.gameplay.money
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=slot.rect.center
        )

        self.gameplay.handle_event(event)

        self.assertTrue(self.gameplay.wave_state.active)
        self.assertIs(self.gameplay.selected_tower_type, FirewallPulse)
        self.assertEqual(self.gameplay.money, money)
        self.assertEqual(self.gameplay.towers, [])
        self.assertFalse(slot.occupied)
        self.assertTrue(slot.selected)
        self.assertTrue(slot.hovering)

    def test_banner_click_does_not_start_from_pause_or_finished_game(
        self,
    ):
        """Respect pause, loss, and victory before handling a click."""
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=self.gameplay.wave_ready_rect.center,
        )
        for state in ("paused", "game_over", "won"):
            with self.subTest(state=state):
                self.gameplay.paused = state == "paused"
                self.gameplay.game_over = state == "game_over"
                self.gameplay.wave_state.won = state == "won"
                if self.gameplay.paused:
                    self.gameplay.pause_start_time = pygame.time.get_ticks()

                self.gameplay.handle_event(event)

                self.assertFalse(self.gameplay.wave_state.active)
                self.assertEqual(self.gameplay.enemy_state.spawn_queue, [])

    def test_space_key_still_starts_the_ready_wave(self):
        """Keep the original keyboard control for starting waves."""
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

        self.gameplay.handle_event(event)

        self.assertTrue(self.gameplay.wave_state.active)
        self.assertFalse(self.gameplay.wave_state.next_ready)
        self.assertTrue(self.gameplay.enemy_state.spawn_queue)

    def test_screens_and_first_enemy_render(self):
        """Draw each screen and an active wave using the real assets."""
        self.app.get_main_menu()
        self.app.current_screen.update(1 / 60)
        self.app.current_screen.draw(self.app.window)
        self.app.get_map_selection()
        self.app.current_screen.draw(self.app.window)
        self.app.get_settings()
        self.app.current_screen.draw(self.app.window)
        self.app.pop_screen()
        self.app.change_screen(self.gameplay)
        self.gameplay.start_wave()
        self.gameplay.update(1 / 60)
        self.gameplay.draw(self.app.window)
        self.assertEqual(len(self.gameplay.enemy_state.enemies), 1)
        Tutorial(self.app).draw(self.app.window)

    def test_quit_event_exits_main_loop(self):
        """Stop the loop after the game window receives a quit event."""
        code = (
            "import pygame; from program_files.app import App; "
            "app = App(); pygame.event.post(pygame.event.Event("
            "pygame.QUIT)); app.run(); assert not pygame.get_init()"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=15,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
