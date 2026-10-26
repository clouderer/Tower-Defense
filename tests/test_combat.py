"""Check movement, spawning, tower targets, and sprite animation."""


# @generated fully ChatGPT 6.1 Sol: Tests

import unittest

import pygame

from program_files.screen.types.gameplay.enemy import (
    Glitchworm,
    LeakedFile,
    PingFlooder,
    Ransomware,
    TrojanFile,
)
from program_files.screen.types.gameplay.tower.bitblaster import BitBlaster
from program_files.screen.types.gameplay.tower.clock_throttler import (
    ClockThrottler,
)
from program_files.screen.types.gameplay.tower.firewall_pulse import (
    FirewallPulse,
)
from program_files.screen.types.gameplay.tower.proxy_beam import ProxyBeam
from program_files.screen.types.gameplay.tower_slot.tower_slot import (
    TowerSlot,
)
from program_files.ui.sprite import Sprite
from program_files.ui.text_object import get_font


ENEMY_TYPES = (Glitchworm, PingFlooder, Ransomware, TrojanFile, LeakedFile)
TOWER_TYPES = (BitBlaster, ClockThrottler, FirewallPulse, ProxyBeam)


class CombatRegressionTests(unittest.TestCase):
    """Check enemy movement, tower targets, spawning, and animation."""

    @classmethod
    def setUpClass(cls):
        """Initialize Pygame and a display for loading sprite images."""
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        """Clear cached fonts before closing Pygame."""
        get_font.cache_clear()
        pygame.quit()

    def test_enemy_movement_keeps_distance_across_corners(self):
        """Keep movement distance equal when updates cross corners."""
        path = [(0, 0), (5, 0), (5, 5), (0, 5), (0, -1000)]

        for enemy_type in ENEMY_TYPES:
            for level in (1, len(enemy_type.LEVELS)):
                with self.subTest(enemy=enemy_type.__name__, level=level):
                    large_step = enemy_type(path, level=level)
                    small_steps = enemy_type(path, level=level)
                    duration = 24 / large_step.speed

                    large_step.update(duration)
                    for step in range(24):
                        small_steps.update(duration / 24)

                    for enemy in (large_step, small_steps):
                        self.assertAlmostEqual(enemy.x_position, 0)
                        self.assertAlmostEqual(enemy.y_position, -4)
                        self.assertEqual(enemy.current_waypoint, 4)
                        self.assertEqual(enemy.direction, "up")
                        self.assertFalse(enemy.reached_end)

                    self.assertAlmostEqual(
                        large_step.x_position, small_steps.x_position
                    )
                    self.assertAlmostEqual(
                        large_step.y_position, small_steps.y_position
                    )

    def test_enemy_can_finish_route_in_one_update(self):
        """Finish the route when an update covers its full length."""
        path = [(0, 0), (5, 0), (5, 5), (0, 5)]

        for enemy_type in ENEMY_TYPES:
            with self.subTest(enemy=enemy_type.__name__):
                enemy = enemy_type(path)
                enemy.update(100 / enemy.speed)

                self.assertTrue(enemy.reached_end)
                self.assertEqual((enemy.x_position, enemy.y_position), (0, 5))
                self.assertEqual(enemy.distance_to_finish, 0)

                enemy.update(1)
                self.assertEqual((enemy.x_position, enemy.y_position), (0, 5))

    def test_trojan_cap_does_not_build_up_spawnling_bursts(self):
        """Keep the spawn interval after a Trojan reaches its limit."""
        path = [(0, 0), (1000000, 0)]

        for level in range(1, len(TrojanFile.LEVELS) + 1):
            with self.subTest(level=level):
                trojan = TrojanFile(path, level=level)
                interval = trojan.SPAWNLING_INTERVALS[level - 1]
                active_limit = trojan.MAX_ACTIVE_SPAWNLINGS[level - 1]
                for spawnling_index in range(active_limit):
                    trojan.register_spawnling(LeakedFile(path, level=level))

                trojan.update(interval * 10)
                self.assertIsNone(trojan.consume_spawnling())

                trojan.spawnlings[0].is_alive = False
                trojan.update(0.01)
                spawnling_path = trojan.consume_spawnling()
                self.assertIsNotNone(spawnling_path)
                trojan.register_spawnling(
                    LeakedFile(spawnling_path, level=level)
                )
                self.assertEqual(len(trojan.spawnlings), active_limit)

                trojan.spawnlings[0].is_alive = False
                trojan.update(0.01)
                self.assertIsNone(trojan.consume_spawnling())

                trojan.update(interval * 0.9)
                self.assertIsNone(trojan.consume_spawnling())
                trojan.update(interval * 0.11)
                self.assertIsNotNone(trojan.consume_spawnling())

    def test_clock_target_controls_glow_and_clears(self):
        """Select a target in range and clear the glow afterward."""
        tower = ClockThrottler(TowerSlot((20, 20)))
        center_x, center_y = tower.rect.center
        farther_from_exit = Glitchworm(
            [(center_x, center_y), (center_x + 100, center_y)]
        )
        nearer_to_exit = Glitchworm(
            [(center_x + 1, center_y), (center_x + 50, center_y)]
        )
        outside_range = Glitchworm(
            [(center_x + 1000, center_y), (center_x + 1001, center_y)]
        )
        dead_enemy = Glitchworm(
            [(center_x, center_y), (center_x + 1, center_y)]
        )
        dead_enemy.is_alive = False
        finished_enemy = Glitchworm(
            [(center_x, center_y), (center_x + 1, center_y)]
        )
        finished_enemy.reached_end = True

        tower.find_target([
            farther_from_exit, nearer_to_exit, outside_range,
            dead_enemy, finished_enemy,
        ])
        self.assertIs(tower.target, nearer_to_exit)
        self.assertEqual(
            tower.enemies_in_range, [farther_from_exit, nearer_to_exit]
        )
        tower.update(0.5)
        self.assertGreater(tower.glow_alpha, 0)

        tower.find_target([])
        tower.update(1)
        self.assertIsNone(tower.target)
        self.assertEqual(tower.enemies_in_range, [])
        self.assertEqual(tower.glow_alpha, 0)

    def test_sprite_advances_multiple_frames_and_wraps(self):
        """Advance every elapsed frame and wrap at the sheet's end."""
        sprite = Sprite(
            Glitchworm.DIRECTION_SPRITES["right"],
            x_cnt=8,
            y_cnt=1,
            fps=18,
        )
        sprite.update(0.25)
        self.assertEqual(sprite.frame_index, 4)
        self.assertIs(sprite.image, sprite.frames[4])

        sprite.update(0.25)
        self.assertEqual(sprite.frame_index, 1)
        self.assertIs(sprite.image, sprite.frames[1])

        sprite.update(0.01)
        self.assertEqual(sprite.frame_index, 1)
        sprite.update(0.05)
        self.assertEqual(sprite.frame_index, 2)

    def test_towers_stop_upgrading_at_maximum_level(self):
        """Prevent further upgrades after the final tower level."""
        for tower_type in TOWER_TYPES:
            with self.subTest(tower=tower_type.__name__):
                tower = tower_type(TowerSlot((20, 20)))
                while tower.level < len(tower.UPGRADE_LEVELS):
                    self.assertTrue(tower.can_upgrade)
                    self.assertIsNotNone(tower.next_upgrade_cost)
                    self.assertTrue(tower.upgrade())

                final_stats = (
                    tower.level, tower.range, tower.damage,
                    tower.attack_cooldown,
                )
                self.assertFalse(tower.can_upgrade)
                self.assertIsNone(tower.next_upgrade_cost)
                self.assertFalse(tower.upgrade())
                self.assertEqual(
                    (
                        tower.level, tower.range, tower.damage,
                        tower.attack_cooldown,
                    ),
                    final_stats,
                )
