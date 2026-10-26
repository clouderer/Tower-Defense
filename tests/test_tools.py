"""Check automation against live game controls, stats, and reports."""

from contextlib import redirect_stdout
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.gameplay import Gameplay
from program_files.ui.sprite import Sprite
from tools import simulate_balance as balance
from tools.compare_builds import ClockTierShop
from tools.compare_hybrids import HybridShop
from tools.play_balance import VisibleCampaign
from tools.runtime import pygame_session
from tools.ui_tower_shop import UiTowerShop


def simulation_settings(**changes):
    settings = dict(
        strategy="mixed-upgrades", step_ms=20, buy_during_wave=True,
        starter_firewalls=1, reserve_slots=len(NEON_GRID_MAP.tower_positions),
        max_seconds=1, enemy_health_scale=1, enemy_speed_scale=1,
        spawn_interval_ms=None,
    )
    return SimpleNamespace(**(settings | changes))


class ToolTests(unittest.TestCase):
    def test_simulation_reports_timeout_and_live_configuration(self):
        with redirect_stdout(io.StringIO()):
            result = balance.simulate(simulation_settings())
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["game_seconds"], 1)
        self.assertEqual(result["waves_cleared"], 0)
        config = result["configuration"]
        self.assertEqual(config["start_money"], Gameplay.START_MONEY)
        self.assertEqual(config["spawn_interval_ms"],
                         Gameplay.ENEMY_SPAWN_INTERVAL)
        self.assertEqual(config["towers"]["ClockThrottler"]["cost"],
                         balance.ClockThrottler.COST)
        self.assertEqual(len(config["source_sha256"]), 64)
        self.assertFalse(pygame.get_init())

    def test_failed_simulation_restores_stats_sdl_and_sprite_loader(self):
        levels = {enemy: enemy.LEVELS for enemy in balance.ENEMY_TYPES}
        interval = Gameplay.ENEMY_SPAWN_INTERVAL
        loader = Sprite.get_frames
        drivers = {key: os.environ.get(key) for key in (
            "SDL_VIDEODRIVER", "SDL_AUDIODRIVER",
        )}
        with (
            redirect_stdout(io.StringIO()),
            patch.object(Gameplay, "update", side_effect=RuntimeError("test")),
            self.assertRaisesRegex(RuntimeError, "test"),
        ):
            balance.simulate(simulation_settings(
                enemy_health_scale=2, enemy_speed_scale=0.5,
                spawn_interval_ms=200,
            ))
        for enemy, original in levels.items():
            self.assertIs(enemy.LEVELS, original)
        self.assertEqual(Gameplay.ENEMY_SPAWN_INTERVAL, interval)
        self.assertIs(Sprite.get_frames, loader)
        self.assertFalse(pygame.get_init())
        for key, value in drivers.items():
            self.assertEqual(os.environ.get(key), value)

    def test_ui_shop_places_upgrades_and_sells_all_current_towers(self):
        with pygame_session(headless=True):
            app = App()
            app.get_gameplay(NEON_GRID_MAP)
            game = app.current_screen
            records = []
            shop = UiTowerShop(game, "efficient", len(game.tower_slots),
                               record_action=records.append)
            for tower_type in game.TOWER_SELECTION:
                with self.subTest(tower=tower_type.__name__):
                    cost = tower_type.COST + sum(
                        stats.upgrade_cost or 0
                        for stats in tower_type.UPGRADE_LEVELS
                    )
                    game.money = cost
                    slot = game.tower_slots[0]
                    shop.place_tower(tower_type, slot)
                    tower = game.towers[-1]
                    while tower.can_upgrade:
                        shop.upgrade_tower(tower)
                    self.assertEqual(game.money, 0)
                    self.assertEqual(tower.total_cost, cost)
                    self.assertEqual(tower.level,
                                     len(tower_type.UPGRADE_LEVELS))
                    shop.click(tower.rect.center)
                    shop.click(game.sell_button.rect.center)
                    self.assertEqual(game.money, cost)
                    self.assertFalse(slot.occupied)
                    self.assertEqual(game.towers, [])
            self.assertEqual(len(records), sum(
                len(tower.UPGRADE_LEVELS) for tower in game.TOWER_SELECTION
            ))

    def test_shop_coverage_uses_current_tower_positions_and_ranges(self):
        with pygame_session(headless=True):
            app = App()
            app.get_gameplay(NEON_GRID_MAP)
            game = app.current_screen
            shop = balance.TowerShop(game, "efficient", len(game.tower_slots))
            slot = game.tower_slots[0]
            for tower_type in game.TOWER_SELECTION:
                tower = tower_type(slot)
                for level in range(1, len(tower_type.UPGRADE_LEVELS) + 1):
                    with self.subTest(tower=tower_type.__name__, level=level):
                        expected = tuple(
                            index for index, sample in enumerate(shop.samples)
                            if math.dist(tower.rect.center, sample[:2])
                            <= tower.range
                        )
                        self.assertEqual(shop.coverage(
                            tower_type, slot.rect.center, level,
                        ), expected)
                        tower.upgrade()

    def test_specialized_shops_use_current_prices_and_upgrade_rules(self):
        with pygame_session(headless=True):
            for shop_type, options, expected_type, level in (
                (ClockTierShop, {"switch_wave": 1, "clock_level": 2},
                 balance.ClockThrottler, 2),
                (HybridShop, {"switch_wave": 1, "proxy_after": 0},
                 balance.ProxyBeam, 3),
            ):
                with self.subTest(shop=shop_type.__name__):
                    app = App()
                    app.get_gameplay(NEON_GRID_MAP)
                    game = app.current_screen
                    cost = expected_type.COST + sum(
                        stats.upgrade_cost or 0
                        for stats in expected_type.UPGRADE_LEVELS[:level - 1]
                    )
                    game.money = cost
                    shop = shop_type(game, "mixed-upgrades", 2, **options)
                    shop.buy()
                    self.assertEqual(len(game.towers), 1)
                    self.assertIs(type(game.towers[0]), expected_type)
                    self.assertEqual(game.towers[0].level, level)
                    self.assertEqual(game.money, 0)

    def test_headless_ui_runner_opens_menus_and_saves_timeout_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(
                output=directory, headless=True, strategy="mixed-upgrades",
                starter_firewalls=1, step_ms=20, max_seconds=1,
                steps_per_frame=30, render_fps=60, linger=0,
            )
            campaign = VisibleCampaign(args)
            with (
                pygame_session(headless=True),
                patch("pygame.time.get_ticks", campaign.get_ticks),
                redirect_stdout(io.StringIO()),
            ):
                result = campaign.run()
                self.assertIsInstance(campaign.game, Gameplay)
                self.assertEqual(result["status"], "timeout")
                self.assertEqual(result["waves_cleared"], 0)
                self.assertEqual(result["game_seconds"], 1)
                self.assertTrue(campaign.actions)
                saved = json.loads((Path(directory) / "summary.json")
                                   .read_text(encoding="utf-8"))
                self.assertEqual(saved, result)
                screenshot = pygame.image.load(
                    str(Path(directory) / "result.png"),
                )
                self.assertEqual(screenshot.get_size(), (
                    App.DISPLAY_WIDTH, App.DISPLAY_HEIGHT,
                ))

    def test_audit_timeout_is_not_reported_as_defeat(self):
        for skip in (False, True):
            with (
                self.subTest(skip=skip),
                tempfile.TemporaryDirectory() as directory,
            ):
                output = Path(directory) / "audit.json"
                result = subprocess.run(
                    [sys.executable, "-m", "tools.audit_campaign",
                     "--max-seconds", "1", "--step-ms", "1000",
                     "--output", str(output),
                     *(["--skip-waves"] if skip else [])],
                    cwd=Path(__file__).resolve().parents[1],
                    capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                audit = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(audit["status"], "timeout")
                self.assertTrue(audit["money_accounting_valid"])
                self.assertEqual(audit["waves_cleared"], 0)
                self.assertEqual(audit["waves_rewarded"], int(skip))
                self.assertEqual(audit["configuration"]["max_waves"],
                                 len(balance.WAVE_COMPOSITIONS))

    def test_cli_rejects_invalid_policy_and_timing(self):
        for module, arguments in (
            ("simulate_balance", ["--max-seconds", "0"]),
            ("audit_campaign", ["--strategy", "typo", "--output", "unused"]),
            ("compare_builds", ["--coverage-bias", "nan"]),
            ("compare_hybrids", ["--switch-wave", "999"]),
        ):
            with self.subTest(module=module):
                result = subprocess.run(
                    [sys.executable, "-m", f"tools.{module}", *arguments],
                    cwd=Path(__file__).resolve().parents[1],
                    capture_output=True, text=True, timeout=15,
                )
                self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == "__main__":
    unittest.main()
