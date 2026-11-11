"""Check live volume controls and tower sound playback."""

import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy.enemy import Enemy
from program_files.screen.types.gameplay.tower.bitblaster import BitBlaster
from program_files.screen.types.gameplay.tower.clock_throttler import (
    ClockThrottler,
)
from program_files.screen.types.gameplay.tower.firewall_pulse import (
    FirewallPulse,
)
from program_files.screen.types.gameplay.tower.proxy_beam import ProxyBeam
from program_files.ui.text_object import get_font


class AudioSettingsTests(unittest.TestCase):
    """Check sliders, attack cooldowns, and the clock hum in Pygame."""

    @classmethod
    def tearDownClass(cls):
        get_font.cache_clear()
        pygame.quit()

    def setUp(self):
        self.app = App()
        self.app.get_gameplay(NEON_GRID_MAP)
        self.game = self.app.current_screen

    def tearDown(self):
        self.app.audio.stop()
        pygame.mixer.music.stop()

    def add_tower(self, tower_type):
        slot = self.game.tower_slots[len(self.game.towers)]
        tower = tower_type(slot)
        tower.last_attack_time = 0
        self.game.towers.append(tower)
        return tower

    def enemy_at(self, tower):
        x, y = tower.rect.center
        enemy = Enemy(((x, y), (x + 1000, y)))
        enemy.health = 1000
        self.game.enemy_state.enemies = [enemy]
        return enemy

    def test_music_drag_applies_and_survives_reopening_settings(self):
        self.app.get_settings()
        settings = self.app.current_screen
        slider = settings.music_slider
        settings.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=slider.track.center,
        ))
        self.assertAlmostEqual(self.app.volume.music_volume, 0.5)
        self.assertAlmostEqual(pygame.mixer.music.get_volume(), 0.5)
        settings.handle_event(pygame.event.Event(
            pygame.MOUSEMOTION,
            pos=(slider.track.left - 100, slider.track.centery),
        ))
        self.assertEqual(self.app.volume.music_volume, 0)
        settings.handle_event(pygame.event.Event(
            pygame.MOUSEBUTTONUP, button=1,
            pos=(slider.track.right + 100, slider.track.centery),
        ))
        self.assertEqual(self.app.volume.music_volume, 1)
        self.assertFalse(slider.dragging)
        slider.set_from_mouse(slider.track.left + 75)
        self.app.pop_screen()
        self.app.get_settings()
        self.assertAlmostEqual(self.app.current_screen.music_slider.value,
                               0.25)
        self.assertAlmostEqual(pygame.mixer.music.get_volume(), 0.25)
        self.assertEqual(self.app.volume.sfx_volume, 1)

    def test_sfx_slider_mutes_and_restores_effects_independently(self):
        self.app.get_settings()
        settings = self.app.current_screen
        slider = settings.sfx_slider
        for position, value in ((slider.track.left, 0),
                                (slider.track.right, 1)):
            settings.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1,
                pos=(position, slider.track.centery),
            ))
            settings.handle_event(pygame.event.Event(
                pygame.MOUSEBUTTONUP, button=1,
                pos=(position, slider.track.centery),
            ))
            self.assertEqual(self.app.volume.sfx_volume, value)
            for name, sound in self.app.audio.sounds.items():
                expected = self.app.audio.SOUND_FILES[name][1] * value
                self.assertAlmostEqual(sound.get_volume(), expected,
                                       delta=0.01)
        self.assertEqual(pygame.mixer.music.get_volume(), 1)

    def test_shots_follow_attacks_and_respect_cooldowns(self):
        for tower_type in (BitBlaster, FirewallPulse, ProxyBeam):
            with self.subTest(tower=tower_type.NAME):
                self.game.towers.clear()
                self.app.audio.stop()
                tower = self.add_tower(tower_type)
                enemy = self.enemy_at(tower)
                with patch.object(self.app.audio, "play_shot",
                                  wraps=self.app.audio.play_shot) as play:
                    self.game.update_enemies(5000, 0)
                    play.assert_called_once_with(tower.NAME)
                    self.assertGreater(
                        self.app.audio.sounds[tower.NAME].get_num_channels(),
                        0,
                    )
                    if tower.PROJECTILE_SHEET is not None:
                        self.assertEqual(enemy.health, 1000)
                        self.assertEqual(len(self.game.projectiles), 1)
                    else:
                        self.assertEqual(enemy.health, 1000 - tower.damage)
                    self.game.update_enemies(5001, 0)
                    self.assertEqual(enemy.health, 1000 - tower.damage)
                    self.assertEqual(play.call_count, 1)
                    self.game.update_enemies(5000 + tower.attack_cooldown, 0)
                    self.assertEqual(play.call_count, 2)

    def test_clock_hums_during_cooldown_and_stops_outside_range(self):
        tower = self.add_tower(ClockThrottler)
        enemy = self.enemy_at(tower)
        tower.last_attack_time = 5000
        self.game.update_enemies(5001, 0)
        self.assertEqual(enemy.health, 1000)
        channel = self.app.audio.clock_channel
        self.assertTrue(channel.get_busy())
        self.assertIs(channel.get_sound(),
                      self.app.audio.sounds["CLOCK_THROTTLER"])
        enemy.x_position += 1000
        self.game.update_enemies(5002, 0)
        self.assertFalse(channel.get_busy())

    def test_last_enemy_dying_or_last_clock_being_sold_stops_hum(self):
        tower = self.add_tower(ClockThrottler)
        enemy = self.enemy_at(tower)
        self.game.update_enemies(5000, 0)
        channel = self.app.audio.clock_channel
        self.assertTrue(channel.get_busy())
        enemy.health = 1
        self.game.update_enemies(5000 + tower.attack_cooldown, 0)
        self.assertFalse(channel.get_busy())
        self.enemy_at(tower)
        self.game.update_enemies(6000, 0)
        self.assertTrue(channel.get_busy())
        self.game.sidebar_tower = tower
        self.game.sidebar_tower_idx = 0
        self.game.sell_tower()
        self.game.update_enemies(6001, 0)
        self.assertFalse(channel.get_busy())

    def test_clock_stops_for_pause_settings_game_over_and_menu(self):
        tower = self.add_tower(ClockThrottler)
        self.enemy_at(tower)
        self.game.update_enemies(5000, 0)
        channel = self.app.audio.clock_channel
        self.assertTrue(channel.get_busy())
        self.game.toggle_pause()
        self.assertFalse(channel.get_busy())
        self.game.toggle_pause()
        self.game.update_enemies(5001, 0)
        self.assertTrue(channel.get_busy())
        self.app.get_settings()
        self.assertFalse(channel.get_busy())
        self.app.pop_screen()
        self.game.update_enemies(5002, 0)
        self.assertTrue(channel.get_busy())
        self.game.set_game_over()
        self.assertFalse(channel.get_busy())
        self.app.audio.set_clock_active(True)
        self.app.get_main_menu()
        self.assertFalse(channel.get_busy())

    def test_clear_sound_plays_once_when_the_wave_actually_finishes(self):
        with patch.object(self.app.audio, "play_event",
                          wraps=self.app.audio.play_event) as play:
            self.game.start_wave()
            self.game.skip_wave()
            play.assert_not_called()
            self.game.enemy_state.spawn_queue.clear()
            self.game.update(0)
            play.assert_called_once_with("WAVE_CLEARED")
            self.assertIs(
                self.app.audio.result_channel.get_sound(),
                self.app.audio.sounds["WAVE_CLEARED"],
            )
            self.game.update(0)
            self.assertEqual(play.call_count, 1)

    def test_loss_sound_plays_once_and_uses_the_effects_volume(self):
        tower = self.add_tower(ClockThrottler)
        self.enemy_at(tower)
        self.game.update_enemies(5000, 0)
        with patch.object(self.app.audio, "play_event",
                          wraps=self.app.audio.play_event) as play:
            self.game.health = 0
            self.game.update(0)
            play.assert_called_once_with("GAME_OVER")
            self.assertFalse(self.app.audio.clock_channel.get_busy())
            self.assertIs(
                self.app.audio.result_channel.get_sound(),
                self.app.audio.sounds["GAME_OVER"],
            )
            self.game.update(0)
            self.game.set_game_over()
            self.assertEqual(play.call_count, 1)
            self.app.audio.set_volume(0)
            self.assertEqual(
                self.app.audio.sounds["GAME_OVER"].get_volume(), 0,
            )
