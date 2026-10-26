"""Check the tower range images shown when the sidebar is open."""


# @generated fully ChatGPT 6.1 Sol: Tests

from pathlib import Path
import unittest
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.maps.game_map import NEON_GRID_MAP
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


ASSET_DIRECTORY = Path(__file__).resolve().parents[1] / "asset_files"
EXPECTED_RANGES = (
    (
        FirewallPulse,
        "firewallpulse",
        (
            ("firewall_level_1_75px_sheet.png", 150),
            ("firewall_level_2_85px_sheet.png", 170),
            ("firewall_level_3_100px_sheet.png", 200),
        ),
    ),
    (
        BitBlaster,
        "bitblaster",
        (
            ("bitblaster_level_1_60px_sheet.png", 120),
            ("bitblaster_level_2_70px_sheet.png", 140),
            ("bitblaster_level_3_80px_sheet.png", 160),
        ),
    ),
    (
        ProxyBeam,
        "proxybeam",
        (
            ("proxy_level_1_120px_sheet.png", 240),
            ("proxy_level_2_135px_sheet.png", 270),
            ("proxy_level_3_150px_sheet.png", 300),
        ),
    ),
    (
        ClockThrottler,
        "clockthrottler",
        (
            ("clock_throttler_level_1_90px_sheet.png", 180),
            ("clock_throttler_level_2_105px_sheet.png", 210),
            ("clock_throttler_level_3_120px_sheet.png", 240),
        ),
    ),
)


class TowerRangeTests(unittest.TestCase):
    """Check range assets, animation, upgrades, and sidebar drawing."""

    @classmethod
    def setUpClass(cls):
        """Initialize Pygame and a display for loading range images."""
        pygame.init()
        pygame.display.set_mode((600, 350))

    @classmethod
    def tearDownClass(cls):
        """Clear cached fonts before closing Pygame."""
        get_font.cache_clear()
        pygame.quit()

    def assert_range_frame(
        self,
        tower,
        path,
        diameter,
        frame_index=0,
    ):
        """Compare the current range frame with its expected asset."""
        sprite = tower.underlay_sprite
        self.assertIsNotNone(sprite)
        self.assertEqual(len(sprite.frames), 24)
        self.assertEqual(sprite.image.get_size(), (diameter, diameter))
        self.assertEqual(sprite.rect.center, tower.tower_slot.rect.center)
        self.assertEqual(sprite.frame_index, frame_index)
        self.assertEqual(tower.sprites.sprites(), [sprite])

        sheet = pygame.image.load(path).convert_alpha()
        self.assertEqual(sheet.get_size(), (diameter * 6, diameter * 4))
        expected_frame = sheet.subsurface(
            (frame_index % 6) * diameter,
            (frame_index // 6) * diameter,
            diameter,
            diameter,
        )
        self.assertEqual(
            pygame.image.tostring(sprite.image, "RGBA"),
            pygame.image.tostring(expected_frame, "RGBA"),
        )

    def test_each_level_replaces_and_animates_its_range(self):
        """Use the correct range sheet for every tower level."""
        for tower_type, directory, levels in EXPECTED_RANGES:
            tower = tower_type(TowerSlot((180, 140)))
            for level, (filename, diameter) in enumerate(levels, start=1):
                with self.subTest(tower=tower_type.__name__, level=level):
                    path = ASSET_DIRECTORY / directory / filename
                    self.assertEqual(tower.level, level)
                    self.assertEqual(diameter, tower.range * 2)
                    self.assert_range_frame(tower, path, diameter)

                    sprite = tower.underlay_sprite
                    tower.update(4 / sprite.fps + 0.001)
                    self.assert_range_frame(tower, path, diameter, 4)

                    if level < len(levels):
                        self.assertTrue(tower.upgrade())
                        self.assertIsNot(tower.underlay_sprite, sprite)
                        self.assertNotIn(sprite, tower.sprites)
                    else:
                        self.assertFalse(tower.upgrade())
                        self.assertIs(tower.underlay_sprite, sprite)
                        self.assert_range_frame(tower, path, diameter, 4)

    def test_sidebar_upgrade_draws_the_new_range(self):
        """Keep the sidebar open and show its upgraded range image."""
        app = App()
        app.get_gameplay(NEON_GRID_MAP)
        gameplay = app.current_screen
        for tower_type, directory, levels in EXPECTED_RANGES:
            with self.subTest(tower=tower_type.__name__):
                slot = gameplay.tower_slots[0]
                tower = tower_type(slot)
                gameplay.towers = [tower]
                gameplay.sidebar_tower = tower
                gameplay.sidebar_tower_idx = 0
                gameplay.money = 10000
                event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN,
                    button=1,
                    pos=gameplay.upgrade_button.rect.center,
                )

                for level in (2, 3):
                    previous_sprite = tower.underlay_sprite
                    money_before = gameplay.money
                    cost = tower.next_upgrade_cost
                    gameplay.handle_event(event)

                    self.assertIs(gameplay.sidebar_tower, tower)
                    self.assertEqual(gameplay.sidebar_tower_idx, 0)
                    self.assertEqual(gameplay.money, money_before - cost)
                    self.assertEqual(tower.level, level)
                    self.assertNotIn(previous_sprite, tower.sprites)
                    filename, diameter = levels[level - 1]
                    self.assert_range_frame(
                        tower, ASSET_DIRECTORY / directory / filename,
                        diameter,
                    )

                    with patch.object(
                        tower.sprites, "draw", wraps=tower.sprites.draw
                    ) as draw_range:
                        gameplay.draw(app.window)
                    draw_range.assert_called_once_with(app.window)

                gameplay.sidebar_tower = None
                gameplay.sidebar_tower_idx = None
                with patch.object(
                    tower.sprites, "draw", wraps=tower.sprites.draw
                ) as draw_range:
                    gameplay.draw(app.window)
                draw_range.assert_not_called()


if __name__ == "__main__":
    unittest.main()
