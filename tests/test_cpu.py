"""Check CPU placement, animation, hit flashes, and health tint."""

import unittest
from unittest.mock import Mock, patch

import pygame

from program_files.app import App
from program_files.maps.game_map import GameMap, NEON_GRID_MAP
from program_files.screen.types.gameplay.cpu import CPU
from program_files.screen.types.gameplay.enemy.enemy import Enemy
from program_files.ui.text_object import get_font


class CPUTests(unittest.TestCase):
    """Exercise CPU visuals through the real gameplay state."""

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

    def enemy_near_exit(self, health=9):
        x, y = self.game.game_map.exit_position
        enemy = Enemy(((x - 10, y), (x, y)))
        enemy.speed = 100
        enemy.health = health
        self.game.enemy_state.enemies = [enemy]
        return enemy

    def test_cpu_uses_a_static_base_between_waves_and_after_win(self):
        cpu = self.game.cpu
        self.assertEqual(cpu.rect.center, NEON_GRID_MAP.enemy_path[-1])
        self.assertEqual(cpu.rect.size, (75, 75))
        self.assertEqual(len(cpu.frames), 1)
        sheet = pygame.image.load(CPU.ASSET_DIR / "cpu.png")
        for index, frame in enumerate(cpu.frames):
            expected = sheet.subsurface(index * 75, 0, 75, 75)
            self.assertEqual(pygame.image.tostring(frame, "RGBA"),
                             pygame.image.tostring(expected, "RGBA"))
        self.game.update(1)
        self.assertEqual(cpu.frame_index, 0)
        self.game.wave_state.won = True
        self.game.update(1)
        self.assertEqual(cpu.frame_index, 0)

    def test_cpu_center_comes_from_each_maps_exit(self):
        for endpoint in ((240, 225), (400, 170)):
            with self.subTest(endpoint=endpoint):
                game_map = GameMap(
                    NEON_GRID_MAP.image, ((0, 100), endpoint),
                    NEON_GRID_MAP.tower_positions,
                )
                self.app.get_gameplay(game_map)
                self.assertEqual(self.app.current_screen.cpu.rect.center,
                                 endpoint)

    def test_grey_alpha_tracks_health_and_stays_within_limits(self):
        for health, alpha in ((100, 0), (75, 64), (50, 128), (25, 191),
                              (0, 255), (-20, 255), (120, 0)):
            with self.subTest(health=health):
                self.game.health = health
                self.game.draw_cpu(self.app.window)
                self.assertEqual(self.game.cpu.grey_image.get_alpha(),
                                 alpha)

    def test_an_enemy_reaching_the_exit_flashes_red_once(self):
        enemy = self.enemy_near_exit()
        self.game.update(0.1)
        self.assertTrue(enemy.reached_end)
        self.assertFalse(enemy.is_alive)
        self.assertEqual(self.game.health, 91)
        self.assertEqual(self.game.cpu.flash_remaining, CPU.FLASH_DURATION)
        window = Mock(spec=pygame.Surface)
        self.game.draw_cpu(window)
        self.assertIs(window.blit.call_args_list[1].args[0], CPU.RED_IMAGE)
        self.game.update(CPU.FLASH_DURATION + 0.01)
        self.assertEqual(self.game.cpu.flash_remaining, 0)
        self.assertEqual(self.game.health, 91)
        window.reset_mock()
        self.game.draw_cpu(window)
        self.assertEqual(window.blit.call_count, 2)

    def test_zero_health_is_fully_grey_even_during_a_red_flash(self):
        self.game.health = 10
        self.enemy_near_exit(health=25)
        self.game.update(0.1)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.health, 0)
        self.assertGreater(self.game.cpu.flash_remaining, 0)
        window = Mock(spec=pygame.Surface)
        self.game.draw_cpu(window)
        self.assertIs(window.blit.call_args_list[-1].args[0],
                      self.game.cpu.grey_image)
        self.assertEqual(self.game.cpu.grey_image.get_alpha(), 255)

    def test_pausing_and_settings_freeze_the_cpu_and_its_flash(self):
        cpu = self.game.cpu
        cpu.flash()
        self.game.update(0.05)
        frame, remaining = cpu.frame_index, cpu.flash_remaining
        self.app.get_settings()
        self.app.current_screen.update(1)
        self.game.update(1)
        self.assertEqual(cpu.frame_index, frame)
        self.assertEqual(cpu.flash_remaining, remaining)
        self.app.pop_screen()
        self.game.update(cpu.frame_duration + 0.001)
        # CPU is static; only its flash changes.
        self.assertEqual(cpu.frame_index, frame)
        self.assertLess(cpu.flash_remaining, remaining)

    def test_cpu_is_drawn_before_enemies(self):
        order = []
        with (
            patch.object(self.game, "draw_cpu",
                         side_effect=lambda window: order.append("cpu")),
            patch.object(self.game, "draw_enemies",
                         side_effect=lambda window: order.append("enemies")),
        ):
            self.game.draw(self.app.window)
        self.assertEqual(order, ["cpu", "enemies"])

    def test_new_cpu_does_not_inherit_another_games_grey_overlay(self):
        self.game.health = 0
        self.game.draw_cpu(self.app.window)
        other = CPU(self.game.game_map.exit_position)
        other.draw(self.app.window, 100, 100)
        self.assertEqual(self.game.cpu.grey_image.get_alpha(), 255)
        self.assertEqual(other.grey_image.get_alpha(), 0)
        self.assertEqual(CPU.GREY_IMAGE.get_alpha(), 255)

    def test_dead_enemy_at_the_exit_does_not_flash_or_damage_the_cpu(self):
        enemy = self.enemy_near_exit()
        enemy.reached_end = True
        enemy.is_alive = False
        self.game.update(0)
        self.assertEqual(self.game.health, self.game.MAX_HEALTH)
        self.assertEqual(self.game.cpu.flash_remaining, 0)
