"""Check the Proxy Beam's connected laser, damage, and cleanup."""

import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.beam import Beam
from program_files.screen.types.gameplay.enemy.enemy import Enemy
from program_files.screen.types.gameplay.tower.proxy_beam import ProxyBeam
from program_files.screen.types.gameplay.tower_slot.tower_slot import (
    TowerSlot,
)
from program_files.ui.text_object import get_font


class BeamTests(unittest.TestCase):
    """Check real beam rendering and its connection to combat."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        get_font.cache_clear()
        pygame.quit()

    def make_enemy(self, position):
        x, y = position
        return Enemy(((x, y), (x + 1000, y)))

    def make_beam(self):
        enemy = self.make_enemy((200, 100))
        beam = Beam((100, 100), enemy, 120, ProxyBeam.EMITTER_SHEET,
                    ProxyBeam.IMPACT_SHEET)
        return beam, enemy

    def make_game(self):
        app = App()
        app.get_gameplay(NEON_GRID_MAP)
        game = app.current_screen
        tower = ProxyBeam(game.tower_slots[0])
        tower.last_attack_time = 0
        game.towers = [tower]
        x, y = tower.rect.center
        enemy = self.make_enemy((x + 90, y))
        enemy.health = 1000
        enemy.speed = 0
        game.enemy_state.enemies = [enemy]
        self.addCleanup(app.audio.stop)
        self.addCleanup(pygame.mixer.music.stop)
        return app, game, tower, enemy

    def test_laser_connects_both_ends_immediately_and_loads_real_frames(self):
        beam, enemy = self.make_beam()
        window = pygame.Surface((300, 200), pygame.SRCALPHA)
        beam.draw(window)
        self.assertGreater(window.get_at((150, 100)).a, 0)
        self.assertEqual(beam.start, (100, 100))
        self.assertEqual(beam.end, (200, 100))
        for frames, path in (
            (beam.emitter_frames, ProxyBeam.EMITTER_SHEET),
            (beam.impact_frames, ProxyBeam.IMPACT_SHEET),
        ):
            sheet = pygame.image.load(path)
            self.assertEqual(len(frames), 8)
            for index, frame in enumerate(frames):
                expected = sheet.subsurface(index * 16, 0, 16, 16)
                self.assertEqual(pygame.image.tostring(frame, "RGBA"),
                                 pygame.image.tostring(expected, "RGBA"))

    def test_beam_stays_connected_as_the_enemy_moves(self):
        beam, enemy = self.make_beam()
        enemy.x_position = 180
        enemy.y_position = 120
        beam.update(0.1)
        self.assertEqual(beam.start, (100, 100))
        self.assertEqual(beam.end, (180, 120))
        window = pygame.Surface((300, 200), pygame.SRCALPHA)
        beam.draw(window)
        self.assertGreater(window.get_at((140, 110)).a, 0)
        self.assertEqual(window.get_at((150, 100)).a, 0)

    def test_beam_fades_when_target_dies_escapes_or_leaves_range(self):
        for condition in ("dead", "escaped", "outside"):
            with self.subTest(condition=condition):
                beam, enemy = self.make_beam()
                if condition == "dead":
                    enemy.is_alive = False
                elif condition == "escaped":
                    enemy.reached_end = True
                else:
                    enemy.x_position += 1000
                beam.update(beam.FADE_DURATION / 2)
                self.assertGreater(beam.alpha, 0)
                self.assertLess(beam.alpha, 255)
                beam.update(beam.FADE_DURATION / 2)
                self.assertTrue(beam.finished)
                self.assertEqual(beam.alpha, 0)

    def test_burst_expires_and_drawing_does_not_damage_the_target(self):
        beam, enemy = self.make_beam()
        health = enemy.health
        beam.update(0.1)
        window = pygame.Surface((300, 200), pygame.SRCALPHA)
        beam.draw(window)
        beam.update(1)
        self.assertTrue(beam.finished)
        window.fill((0, 0, 0, 0))
        beam.draw(window)
        self.assertEqual(window.get_bounding_rect().size, (0, 0))
        self.assertEqual(enemy.health, health)

    def test_proxy_damages_once_per_burst_without_travelling_shots(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(5000, 0)
        first_beam = tower.beam
        self.assertIsNotNone(first_beam)
        self.assertEqual(len(game.projectiles), 0)
        self.assertEqual(tower.pending_projectiles, [])
        self.assertEqual(enemy.health, 1000 - tower.damage)
        game.update_towers(0.1)
        game.update_enemies(5001, 0)
        self.assertIs(tower.beam, first_beam)
        self.assertEqual(enemy.health, 1000 - tower.damage)
        game.update_enemies(5000 + tower.attack_cooldown, 0)
        self.assertIsNot(tower.beam, first_beam)
        self.assertEqual(enemy.health, 1000 - tower.damage * 2)

    def test_lethal_hit_keeps_a_brief_beam_and_pays_once(self):
        app, game, tower, enemy = self.make_game()
        enemy.health = tower.damage
        money = game.money
        game.update_enemies(5000, 0)
        self.assertFalse(enemy.is_alive)
        self.assertIsNotNone(tower.beam)
        self.assertEqual(game.money, money + enemy.reward)
        game.update_towers(0.06)
        self.assertIsNotNone(tower.beam)
        game.update_towers(0.06)
        self.assertIsNone(tower.beam)
        game.update_enemies(5001, 0)
        self.assertEqual(game.money, money + enemy.reward)

    def test_beam_freezes_in_settings_and_stops_when_the_tower_is_sold(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(5000, 0)
        game.update_towers(0.1)
        elapsed = tower.beam.elapsed
        app.get_settings()
        app.current_screen.update(1)
        self.assertEqual(tower.beam.elapsed, elapsed)
        app.pop_screen()
        game.update_towers(0.1)
        self.assertGreater(tower.beam.elapsed, elapsed)
        game.sidebar_tower = tower
        game.sidebar_tower_idx = 0
        game.sell_tower()
        self.assertIsNone(tower.beam)

    def test_gameplay_draws_the_beam_and_game_over_removes_it(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(5000, 0)
        with patch.object(tower.beam, "draw",
                          wraps=tower.beam.draw) as draw:
            game.draw(app.window)
            draw.assert_called_once_with(app.window)
        game.set_game_over()
        self.assertIsNone(tower.beam)

    def test_beam_handles_an_enemy_at_the_tower_position(self):
        beam, enemy = self.make_beam()
        enemy.x_position, enemy.y_position = beam.start
        beam.update(0.05)
        beam.draw(pygame.Surface((300, 200), pygame.SRCALPHA))
        self.assertEqual(beam.start, beam.end)
