"""Check boss shielding, tower damage, and the final wave."""


# @generated fully ChatGPT 6.1 Sol: Tests

import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy import (
    Glitchworm,
    KernelPanic,
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
from program_files.ui.text_object import get_font


REGULAR_ENEMY_TYPES = (
    Glitchworm, LeakedFile, PingFlooder, Ransomware, TrojanFile,
)
TOWER_TYPES = (BitBlaster, ClockThrottler, FirewallPulse, ProxyBeam)
LONG_PATH = [(0, 0), (1000000, 0)]


class BossTests(unittest.TestCase):
    """Check the boss's stats, shield, and shared combat handling."""

    @classmethod
    def setUpClass(cls):
        """
        Initialize Pygame and a display for the real sprite assets.
        """
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        """Clear cached fonts before closing Pygame."""
        get_font.cache_clear()
        pygame.quit()

    def test_boss_is_slower_and_has_more_health_than_regular_tanks(
        self,
    ):
        """
        Keep the boss much tougher and slower than regular enemies.
        """
        boss = KernelPanic(LONG_PATH)
        final_tank_health = Ransomware.LEVELS[-1].health
        slowest_final_speed = min(
            enemy_type.LEVELS[-1].speed
            for enemy_type in REGULAR_ENEMY_TYPES
        )

        self.assertGreater(boss.max_health, final_tank_health * 4)
        self.assertLess(boss.speed, slowest_final_speed / 2)
        self.assertLess(
            boss.speed, min(stats.speed for stats in Ransomware.LEVELS)
        )

    def test_regular_enemies_take_full_damage_and_reward_only_once(
        self,
    ):
        """Keep ordinary damage unchanged and pay each kill once."""
        for enemy_type in REGULAR_ENEMY_TYPES:
            with self.subTest(enemy=enemy_type.__name__):
                enemy = enemy_type(LONG_PATH, level=len(enemy_type.LEVELS))
                health = enemy.health

                self.assertEqual(enemy.take_damage(1), 0)
                self.assertEqual(enemy.health, health - 1)
                self.assertTrue(enemy.is_alive)
                self.assertEqual(
                    enemy.take_damage(health * 2), enemy.reward
                )
                self.assertEqual(enemy.health, 0)
                self.assertFalse(enemy.is_alive)
                self.assertEqual(enemy.take_damage(health), 0)
                self.assertEqual(enemy.health, 0)

    def test_finished_enemies_do_not_take_damage_or_give_rewards(self):
        """Ignore attacks after any enemy has reached the exit."""
        for enemy_type in (*REGULAR_ENEMY_TYPES, KernelPanic):
            with self.subTest(enemy=enemy_type.__name__):
                enemy = enemy_type(LONG_PATH)
                enemy.reached_end = True
                health = enemy.health

                self.assertEqual(enemy.take_damage(health * 2), 0)
                self.assertEqual(enemy.health, health)

    def test_shield_activates_at_the_end_of_each_cycle(self):
        """Shield the boss for the final part of each ability cycle."""
        boss = KernelPanic(LONG_PATH)
        shield_start = boss.SHIELD_INTERVAL - boss.SHIELD_DURATION

        self.assertFalse(boss.shield_active)
        boss.update(shield_start - 0.125)
        self.assertFalse(boss.shield_active)
        boss.update(0.125)
        self.assertTrue(boss.shield_active)
        boss.update(boss.SHIELD_DURATION - 0.125)
        self.assertTrue(boss.shield_active)
        boss.update(0.125)
        self.assertFalse(boss.shield_active)
        self.assertAlmostEqual(boss.ability_time, 0)

        boss.update(boss.SHIELD_INTERVAL * 2 + shield_start)
        self.assertTrue(boss.shield_active)
        self.assertAlmostEqual(boss.ability_time, shield_start)

    def test_shield_reduces_damage_and_still_allows_a_kill(self):
        """Reduce shielded damage while keeping one kill reward."""
        boss = KernelPanic(LONG_PATH)
        health = boss.health
        self.assertEqual(boss.take_damage(40), 0)
        self.assertEqual(boss.health, health - 40)
        boss.update(boss.SHIELD_INTERVAL - boss.SHIELD_DURATION)
        health = boss.health

        self.assertEqual(boss.take_damage(40), 0)
        self.assertEqual(
            boss.health, health - 40 * boss.SHIELD_DAMAGE_MULTIPLIER
        )
        lethal_damage = boss.health / boss.SHIELD_DAMAGE_MULTIPLIER + 1
        self.assertEqual(boss.take_damage(lethal_damage), boss.reward)
        self.assertFalse(boss.is_alive)
        self.assertFalse(boss.shield_active)
        self.assertEqual(boss.health, 0)
        self.assertEqual(boss.take_damage(lethal_damage), 0)

    def test_shield_timer_handles_large_and_small_updates_equally(
        self,
    ):
        """
        Keep ability timing consistent across different frame sizes.
        """
        large_step = KernelPanic(LONG_PATH)
        small_steps = KernelPanic(LONG_PATH)
        duration = (
            large_step.SHIELD_INTERVAL * 3 - large_step.SHIELD_DURATION / 2
        )

        large_step.update(duration)
        for step in range(round(duration / 0.125)):
            small_steps.update(0.125)

        self.assertAlmostEqual(
            large_step.ability_time, small_steps.ability_time
        )
        self.assertTrue(large_step.shield_active)
        self.assertEqual(large_step.shield_active, small_steps.shield_active)
        self.assertAlmostEqual(
            large_step.x_position, small_steps.x_position
        )

    def test_dead_or_finished_boss_does_not_advance_its_ability(self):
        """
        Stop the shield and its timer after death or reaching the exit.
        """
        for finished in (False, True):
            with self.subTest(finished=finished):
                boss = KernelPanic(LONG_PATH)
                boss.update(boss.SHIELD_INTERVAL - boss.SHIELD_DURATION)
                self.assertTrue(boss.shield_active)
                boss.is_alive = finished
                boss.reached_end = finished
                ability_time = boss.ability_time

                boss.update(boss.SHIELD_INTERVAL)

                self.assertEqual(boss.ability_time, ability_time)
                self.assertFalse(boss.shield_active)

    def test_all_towers_use_enemy_damage_handling_and_pay_once(self):
        """
        Use the damage hook for normal enemies and a shielded boss.
        """
        for tower_type in TOWER_TYPES:
            for enemy_type in (Glitchworm, KernelPanic):
                with self.subTest(
                    tower=tower_type.__name__, enemy=enemy_type.__name__
                ):
                    tower = tower_type(TowerSlot((40, 40)))
                    center_x, center_y = tower.rect.center
                    enemy = enemy_type([
                        (center_x, center_y), (center_x + 1000000, center_y)
                    ])
                    multiplier = 1
                    if isinstance(enemy, KernelPanic):
                        enemy.update(
                            enemy.SHIELD_INTERVAL - enemy.SHIELD_DURATION
                        )
                        multiplier = enemy.SHIELD_DAMAGE_MULTIPLIER
                    tower.find_target([enemy])
                    self.assertIs(tower.target, enemy)
                    tower.last_attack_time = 0
                    health = enemy.health

                    with patch.object(
                        enemy, "take_damage", wraps=enemy.take_damage
                    ) as take_damage:
                        self.assertEqual(
                            tower.attack(tower.attack_cooldown), 0
                        )
                        take_damage.assert_called_once_with(tower.damage)
                        self.assertEqual(
                            enemy.health, health - tower.damage * multiplier
                        )
                        enemy.health = tower.damage * multiplier
                        self.assertEqual(
                            tower.attack(tower.attack_cooldown * 2),
                            enemy.reward,
                        )
                        self.assertEqual(enemy.health, 0)
                        self.assertFalse(enemy.is_alive)
                        self.assertEqual(
                            tower.attack(tower.attack_cooldown * 3), 0
                        )
                        self.assertEqual(take_damage.call_count, 2)

    def test_pausing_gameplay_stops_the_boss_shield_timer(self):
        """Freeze the shield cycle while gameplay is paused."""
        app = App()
        app.get_gameplay(NEON_GRID_MAP)
        gameplay = app.current_screen
        boss = KernelPanic(gameplay.game_map.enemy_path)
        boss.update(boss.SHIELD_INTERVAL - boss.SHIELD_DURATION - 0.125)
        gameplay.enemy_state.enemies = [boss]
        gameplay.wave_state.active = True
        gameplay.wave_state.next_ready = False
        gameplay.toggle_pause()
        ability_time = boss.ability_time

        gameplay.update(0.25)

        self.assertEqual(boss.ability_time, ability_time)
        self.assertFalse(boss.shield_active)
        gameplay.toggle_pause()
        gameplay.update(0.25)
        self.assertTrue(boss.shield_active)

    def test_final_wave_cannot_clear_while_the_boss_is_alive(self):
        """Require the last boss to die before declaring victory."""
        app = App()
        app.get_gameplay(NEON_GRID_MAP)
        gameplay = app.current_screen
        boss = KernelPanic(gameplay.game_map.enemy_path)
        gameplay.enemy_state.enemies = [boss]
        gameplay.wave_state.round = gameplay.wave_state.MAX_WAVES
        gameplay.wave_state.active = True
        gameplay.wave_state.next_ready = False

        with patch("pygame.time.get_ticks", return_value=1000):
            gameplay.update(0)
        self.assertTrue(gameplay.wave_state.active)
        self.assertFalse(gameplay.wave_state.cleared)
        self.assertFalse(gameplay.wave_state.won)

        boss.take_damage(boss.max_health * 2)
        with patch("pygame.time.get_ticks", return_value=1000):
            gameplay.update(0)
        self.assertTrue(gameplay.wave_state.cleared)
        with patch(
            "pygame.time.get_ticks",
            return_value=1000 + gameplay.wave_state.CLEARED_DELAY,
        ):
            gameplay.update(0)
        self.assertTrue(gameplay.wave_state.won)


if __name__ == "__main__":
    unittest.main()
