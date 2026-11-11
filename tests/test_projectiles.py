"""Check projectile directions, flight, hits, and gameplay cleanup."""

import math
import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy.enemy import Enemy
from program_files.screen.types.gameplay.enemy.kernel_panic import (
    KernelPanic,
)
from program_files.screen.types.gameplay.projectile import (
    Projectile, get_projectile_path,
)
from program_files.screen.types.gameplay.tower.bitblaster import BitBlaster
from program_files.screen.types.gameplay.tower.firewall_pulse import (
    FirewallPulse,
)
from program_files.screen.types.gameplay.tower_slot.tower_slot import (
    TowerSlot,
)
from program_files.ui.text_object import get_font


class ProjectileTests(unittest.TestCase):
    """Use the real sheet and enemies to check travelling attacks."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        Projectile.get_frames.cache_clear()
        get_font.cache_clear()
        pygame.quit()

    def make_enemy(self, position):
        x, y = position
        return Enemy(((x, y), (x + 1000, y)))

    def make_projectile(self, end, start=(100, 100), damage=2, speed=100,
                        impact=False):
        enemy = self.make_enemy(end)
        return Projectile(
            BitBlaster.PROJECTILE_SHEET, start, enemy, damage, speed,
            impact_sheet=BitBlaster.IMPACT_SHEET if impact else None,
        )

    def make_game(self, tower_type=BitBlaster):
        app = App()
        app.get_gameplay(NEON_GRID_MAP)
        game = app.current_screen
        tower = tower_type(game.tower_slots[0])
        tower.last_attack_time = 0
        game.towers.append(tower)
        x, y = tower.rect.center
        enemy = self.make_enemy((x + 48, y))
        enemy.speed = 0
        game.enemy_state.enemies = [enemy]
        self.addCleanup(app.audio.stop)
        self.addCleanup(pygame.mixer.music.stop)
        return app, game, tower, enemy

    def test_all_eight_directions_select_the_correct_row(self):
        directions = (
            (0, -100), (100, -100), (100, 0), (100, 100),
            (0, 100), (-100, 100), (-100, 0), (-100, -100),
        )
        sheet = pygame.image.load(BitBlaster.PROJECTILE_SHEET)
        for row, (dx, dy) in enumerate(directions):
            with self.subTest(row=row):
                end = (100 + dx, 100 + dy)
                shot = self.make_projectile(end)
                self.assertEqual(shot.path.direction_row, row)
                self.assertEqual(len(shot.frames), 8)
                for column, frame in enumerate(shot.frames):
                    expected = sheet.subsurface(column * 16, row * 16,
                                                16, 16)
                    self.assertEqual(pygame.image.tostring(frame, "RGBA"),
                                     pygame.image.tostring(expected, "RGBA"))
                self.assertEqual(shot.path.position_at(1000), end)

    def test_direction_boundaries_choose_the_nearest_direction(self):
        for angle, row in ((22.4, 0), (22.6, 1), (337.4, 7), (337.6, 0)):
            radians = math.radians(angle)
            end = (math.sin(radians) * 100, -math.cos(radians) * 100)
            self.assertEqual(get_projectile_path((0, 0), end).direction_row,
                             row)

    def test_projectile_animates_and_tracks_a_moving_enemy(self):
        shot = self.make_projectile((160, 100))
        health = shot.target.health
        self.assertEqual(shot.update(0.2), 0)
        self.assertEqual(shot.position, (120, 100))
        self.assertEqual(shot.frame_index, 6)
        self.assertEqual(shot.target.health, health)
        shot.target.y_position = 125
        shot.update(0.1)
        self.assertEqual(shot.path.direction_row, 3)
        self.assertEqual(shot.target.health, health)
        shot.update(1)
        self.assertEqual(shot.position, (160, 125))
        self.assertEqual(shot.target.health, health - shot.damage)
        self.assertTrue(shot.finished)

    def test_zero_length_path_hits_once_without_dividing_by_zero(self):
        shot = self.make_projectile((100, 100), damage=1000)
        self.assertEqual(shot.path.distance, 0)
        self.assertEqual(shot.update(0), shot.target.reward)
        self.assertEqual(shot.target.health, 0)
        self.assertEqual(shot.update(1), 0)

    def test_large_step_hits_once_without_overshooting(self):
        shot = self.make_projectile((150, 100), damage=1000)
        group = pygame.sprite.Group(shot)
        self.assertEqual(shot.update(10), shot.target.reward)
        self.assertEqual(shot.position, (150, 100))
        self.assertFalse(group.has(shot))
        self.assertEqual(shot.update(10), 0)

    def test_dead_and_escaped_targets_cancel_the_shot(self):
        for state in ("dead", "escaped"):
            with self.subTest(state=state):
                shot = self.make_projectile((150, 100), damage=1000,
                                            impact=True)
                group = pygame.sprite.Group(shot)
                if state == "dead":
                    shot.target.is_alive = False
                else:
                    shot.target.reached_end = True
                health = shot.target.health
                self.assertEqual(shot.update(10), 0)
                self.assertEqual(shot.target.health, health)
                self.assertFalse(group.has(shot))
                self.assertIsNone(shot.impact)

    def test_boss_shield_is_checked_at_impact(self):
        boss = KernelPanic(((150, 100), (1150, 100)))
        shot = Projectile(BitBlaster.PROJECTILE_SHEET, (100, 100),
                          boss, 10, 100)
        boss.ability_time = boss.SHIELD_INTERVAL - boss.SHIELD_DURATION
        shot.update(1)
        self.assertEqual(boss.health, boss.max_health - 5)

    def test_gameplay_rewards_only_when_the_projectile_hits(self):
        app, game, tower, enemy = self.make_game()
        enemy.health = tower.damage
        money = game.money
        game.update_enemies(1000, 0)
        self.assertEqual(len(game.projectiles), 1)
        self.assertEqual(game.money, money)
        self.assertTrue(enemy.is_alive)
        game.update_enemies(1001, 0.1)
        self.assertTrue(enemy.is_alive)
        self.assertEqual(game.money, money)
        game.update_enemies(1002, 0.1)
        self.assertFalse(enemy.is_alive)
        self.assertEqual(game.money, money + enemy.reward)
        self.assertEqual(len(game.projectiles), 0)
        game.update_enemies(1003, 1)
        self.assertEqual(game.money, money + enemy.reward)

    def test_pause_freezes_flight_and_selling_does_not_remove_a_shot(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(1000, 0)
        shot = game.projectiles.sprites()[0]
        position = shot.position
        game.toggle_pause()
        game.update(1)
        self.assertEqual(shot.position, position)
        app.get_settings()
        app.current_screen.update(1)
        self.assertEqual(shot.position, position)
        app.pop_screen()
        game.toggle_pause()
        game.sidebar_tower = tower
        game.sidebar_tower_idx = 0
        game.sell_tower()
        self.assertTrue(game.projectiles.has(shot))
        game.update_projectiles(1)
        self.assertEqual(enemy.health, enemy.max_health - shot.damage)
        self.assertEqual(len(game.projectiles), 0)

    def test_game_over_clears_shots_without_applying_damage(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(1000, 0)
        self.assertEqual(len(game.projectiles), 1)
        game.set_game_over()
        self.assertEqual(len(game.projectiles), 0)
        self.assertEqual(enemy.health, enemy.max_health)

    def test_impact_plays_the_six_frames_once_at_the_hit_position(self):
        shot = self.make_projectile((150, 100), impact=True)
        shot.update(0.25)
        self.assertIsNone(shot.impact)
        shot.update(0.25)
        impact = shot.impact
        self.assertIsNotNone(impact)
        self.assertEqual(len(impact.frames), 6)
        self.assertEqual(impact.rect.center, (150, 100))
        group = pygame.sprite.Group(impact)
        sheet = pygame.image.load(BitBlaster.IMPACT_SHEET)
        for index in range(6):
            self.assertEqual(impact.frame_index, index)
            expected = sheet.subsurface(index * 16, 0, 16, 16)
            self.assertEqual(pygame.image.tostring(impact.image, "RGBA"),
                             pygame.image.tostring(expected, "RGBA"))
            impact.update(impact.frame_duration + 0.000001)
        self.assertFalse(group.has(impact))
        impact.update(1)
        self.assertFalse(group.has(impact))

    def test_lethal_hit_keeps_impact_after_the_enemy_is_gone(self):
        shot = self.make_projectile((150, 100), damage=1000, impact=True)
        self.assertEqual(shot.update(1), shot.target.reward)
        self.assertFalse(shot.target.is_alive)
        impact = shot.impact
        self.assertIsNotNone(impact)
        shot.target.x_position += 100
        impact.update(0.04)
        self.assertEqual(impact.rect.center, (150, 100))
        self.assertEqual(shot.update(1), 0)
        self.assertIs(shot.impact, impact)

    def test_impact_freezes_on_pause_and_game_over_clears_it(self):
        app, game, tower, enemy = self.make_game()
        game.update_enemies(1000, 0)
        self.assertEqual(len(game.impacts), 0)
        game.update_enemies(1001, 0.2)
        self.assertEqual(len(game.projectiles), 0)
        self.assertEqual(len(game.impacts), 1)
        impact = game.impacts.sprites()[0]
        game.update_towers(0.04)
        self.assertEqual(impact.frame_index, 1)
        game.toggle_pause()
        game.update(1)
        self.assertEqual(impact.frame_index, 1)
        app.get_settings()
        app.current_screen.update(1)
        self.assertEqual(impact.frame_index, 1)
        app.pop_screen()
        game.toggle_pause()
        game.update_towers(1)
        self.assertEqual(len(game.impacts), 0)
        game.impacts.add(impact)
        game.set_game_over()
        self.assertEqual(len(game.impacts), 0)

    def test_other_towers_can_use_the_shared_impact_configuration(self):
        with (
            patch.object(FirewallPulse, "PROJECTILE_SHEET",
                         BitBlaster.PROJECTILE_SHEET),
            patch.object(FirewallPulse, "IMPACT_SHEET",
                         BitBlaster.IMPACT_SHEET),
        ):
            tower = FirewallPulse(TowerSlot((100, 100)))
            x, y = tower.rect.center
            enemy = self.make_enemy((x + 20, y))
            shot = tower.create_projectile(enemy)
            shot.update(1)
            self.assertIsNotNone(shot.impact)
            self.assertEqual(len(shot.impact.frames), 6)
            self.assertEqual(shot.impact.rect.center, (x + 20, y))

    def test_firewall_uses_its_own_direction_rows_and_impact_frames(self):
        tower = FirewallPulse(TowerSlot((100, 100)))
        sheet = pygame.image.load(FirewallPulse.PROJECTILE_SHEET)
        impact_sheet = pygame.image.load(FirewallPulse.IMPACT_SHEET)
        directions = (
            (0, -50), (35, -35), (50, 0), (35, 35),
            (0, 50), (-35, 35), (-50, 0), (-35, -35),
        )
        x, y = tower.rect.center
        for row, (dx, dy) in enumerate(directions):
            with self.subTest(row=row):
                enemy = self.make_enemy((x + dx, y + dy))
                shot = tower.create_projectile(enemy)
                self.assertEqual(shot.path.direction_row, row)
                for column, frame in enumerate(shot.frames):
                    expected = sheet.subsurface(column * 16, row * 16,
                                                16, 16)
                    self.assertEqual(pygame.image.tostring(frame, "RGBA"),
                                     pygame.image.tostring(expected, "RGBA"))
                health = enemy.health
                shot.update(0.05)
                self.assertEqual(enemy.health, health)
                self.assertIsNone(shot.impact)
                shot.update(1)
                self.assertEqual(enemy.health, health - tower.damage)
                self.assertEqual(shot.impact.rect.center, (x + dx, y + dy))
                for column, frame in enumerate(shot.impact.frames):
                    expected = impact_sheet.subsurface(column * 16, 0,
                                                       16, 16)
                    self.assertEqual(pygame.image.tostring(frame, "RGBA"),
                                     pygame.image.tostring(expected, "RGBA"))

    def test_firewall_hit_in_gameplay_pays_once_and_leaves_an_impact(self):
        app, game, tower, enemy = self.make_game(FirewallPulse)
        enemy.health = tower.damage
        money = game.money
        game.update_enemies(1000, 0)
        self.assertEqual(enemy.health, tower.damage)
        self.assertEqual(game.money, money)
        self.assertEqual(len(game.projectiles), 1)
        self.assertEqual(len(game.impacts), 0)
        game.update_enemies(1001, 0.2)
        self.assertFalse(enemy.is_alive)
        self.assertEqual(game.money, money + enemy.reward)
        self.assertEqual(len(game.projectiles), 0)
        self.assertEqual(len(game.impacts), 1)
        game.update_enemies(1002, 0.2)
        self.assertEqual(game.money, money + enemy.reward)
        self.assertEqual(len(game.impacts), 1)
        game.update_towers(1)
        self.assertEqual(len(game.impacts), 0)
