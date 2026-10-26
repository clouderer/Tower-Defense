"""Exercise overlapping waves, rewards, and timers in real gameplay."""

from collections import Counter
import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy import LeakedFile, TrojanFile
from program_files.screen.types.gameplay.enemy.wave_config import (
    WAVE_COMPOSITIONS,
)
from program_files.screen.types.gameplay.gameplay import WaveState
from program_files.ui.text_object import get_font


class WaveRuntimeTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        get_font.cache_clear()
        pygame.quit()

    def setUp(self):
        clock = patch("pygame.time.get_ticks", return_value=0)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        self.app = App()
        self.app.get_gameplay(NEON_GRID_MAP)
        self.game = self.app.current_screen

    def start_overlapping_waves(self):
        self.game.start_wave()
        self.game.update(0)
        self.clock.return_value = 400
        self.game.handle_event(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_s,
        ))

    def test_campaign_limit_matches_current_wave_configuration(self):
        self.assertEqual(WaveState.MAX_WAVES, len(WAVE_COMPOSITIONS))

    def test_skip_preserves_enemies_and_each_waves_spawn_clock(self):
        self.start_overlapping_waves()
        game = self.game
        original_enemy = game.enemy_state.enemies[0]
        self.assertEqual(game.wave_state.active_waves, {1, 2})
        self.assertEqual(game.wave_state.rewarded_waves, {1})
        self.assertEqual(
            Counter(spawn.wave_number
                    for spawn in game.enemy_state.spawn_queue),
            {1: 1, 2: 3},
        )
        game.update(0)
        self.assertIn(original_enemy, game.enemy_state.enemies)
        self.assertEqual(
            Counter(enemy.wave_number for enemy in game.enemy_state.enemies),
            {1: 1, 2: 1},
        )
        self.clock.return_value = game.ENEMY_SPAWN_INTERVAL
        game.update(0)
        self.assertEqual(
            Counter(enemy.wave_number for enemy in game.enemy_state.enemies),
            {1: 2, 2: 1},
        )
        self.clock.return_value += 400
        game.update(0)
        self.assertEqual(
            Counter(enemy.wave_number for enemy in game.enemy_state.enemies),
            {1: 2, 2: 2},
        )

    def test_skipped_wave_clears_only_after_queue_and_enemies_finish(self):
        self.start_overlapping_waves()
        game = self.game
        money = game.money
        game.enemy_state.enemies[0].take_damage(1000000)
        game.update(0)
        self.assertIn(1, game.wave_state.active_waves)
        self.clock.return_value = game.ENEMY_SPAWN_INTERVAL
        game.update(0)
        for enemy in game.enemy_state.enemies:
            if enemy.wave_number == 1:
                enemy.take_damage(enemy.health)
        game.update(0)
        self.assertEqual(game.wave_state.active_waves, {2})
        self.assertEqual(game.wave_state.rewarded_waves, {1})
        self.assertEqual(game.money, money)
        self.assertFalse(game.wave_state.cleared)

    def test_pause_adjusts_every_overlapping_spawn_timer(self):
        self.start_overlapping_waves()
        game = self.game
        game.update(0)
        timers = game.enemy_state.wave_spawn_times.copy()
        self.clock.return_value = 1000
        game.toggle_pause()
        self.clock.return_value = 6000
        game.update(5)
        self.assertEqual(game.enemy_state.wave_spawn_times, timers)
        game.toggle_pause()
        self.assertEqual(
            game.enemy_state.wave_spawn_times,
            {wave: value + 5000 for wave, value in timers.items()},
        )
        self.assertEqual(
            game.enemy_state.spawn_time, timers[2] + 5000,
        )

    def test_spawnlings_keep_their_parents_wave_after_skipping(self):
        game = self.game
        game.wave_state.round = 2
        game.wave_state.active_waves = {1}
        trojan = TrojanFile(game.game_map.enemy_path, level=2)
        trojan.wave_number = 1
        trojan.spawnling_timer = trojan.SPAWNLING_INTERVALS[1]
        game.enemy_state.enemies = [trojan]
        game.update(0)
        spawnlings = [enemy for enemy in game.enemy_state.enemies
                      if isinstance(enemy, LeakedFile)]
        self.assertEqual(len(spawnlings), 1)
        self.assertEqual(spawnlings[0].wave_number, 1)
        self.assertEqual(spawnlings[0].level, trojan.level)
        trojan.take_damage(trojan.health)
        game.update(0)
        self.assertIn(1, game.wave_state.active_waves)
        self.assertNotIn(1, game.wave_state.rewarded_waves)
        spawnlings[0].take_damage(spawnlings[0].health)
        game.update(0)
        self.assertNotIn(1, game.wave_state.active_waves)
        self.assertIn(1, game.wave_state.rewarded_waves)

    def test_last_wave_cannot_be_skipped_or_rewarded_early(self):
        game = self.game
        game.wave_state.round = WaveState.MAX_WAVES
        game.start_wave()
        queue = list(game.enemy_state.spawn_queue)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s))
        self.assertFalse(game.can_skip_wave)
        self.assertEqual(game.enemy_state.spawn_queue, queue)
        self.assertEqual(game.wave_state.round, WaveState.MAX_WAVES)
        self.assertEqual(game.wave_state.rewarded_waves, set())


if __name__ == "__main__":
    unittest.main()
