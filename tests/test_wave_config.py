"""Check preset wave counts, enemy levels, and spawn order."""


# @generated fully ChatGPT 6.1 Sol: Tests

from collections import Counter
import unittest

from program_files.screen.types.gameplay.enemy import KernelPanic
from program_files.screen.types.gameplay.enemy.wave_config import (
    MAX_ENEMY_LEVEL,
    MAX_ENEMY_SPAWNING,
    WAVES_PER_ENEMY_LEVEL,
    WAVE_COMPOSITIONS,
    get_wave_spawns,
)


class WaveConfigTests(unittest.TestCase):
    """Keep preset enemies while mixing each wave's spawn order."""

    def test_all_waves_keep_their_preset_enemy_counts(self):
        """Spawn the specified number of each listed enemy."""
        for wave_number, composition in enumerate(WAVE_COMPOSITIONS, 1):
            with self.subTest(wave=wave_number):
                spawns = get_wave_spawns(wave_number)
                expected_counts = Counter(dict(composition))
                actual_counts = Counter(enemy for enemy, level in spawns)

                self.assertEqual(actual_counts, expected_counts)
                self.assertEqual(len(spawns), sum(expected_counts.values()))

    def test_enemy_levels_increase_every_three_waves_and_stop_at_eight(
        self,
    ):
        """Increase enemy levels every three waves and stop at eight."""
        expected_levels = tuple(
            min(
                ((wave_number - 1) // WAVES_PER_ENEMY_LEVEL) + 1,
                MAX_ENEMY_LEVEL,
            )
            for wave_number in range(1, len(WAVE_COMPOSITIONS) + 1)
        )
        self.assertEqual(len(expected_levels), len(WAVE_COMPOSITIONS))

        for wave_number in range(1, len(WAVE_COMPOSITIONS) + 1):
            with self.subTest(wave=wave_number):
                expected_level = expected_levels[wave_number - 1]
                spawns = get_wave_spawns(wave_number)

                for enemy_type, level in spawns:
                    self.assertEqual(
                        level, min(expected_level, len(enemy_type.LEVELS))
                    )

    def test_one_boss_starts_only_the_final_wave(self):
        """Spawn one boss before the final wave's regular enemies."""
        for wave_number in range(1, len(WAVE_COMPOSITIONS) + 1):
            with self.subTest(wave=wave_number):
                spawns = get_wave_spawns(wave_number)
                bosses = [
                    (enemy_type, level) for enemy_type, level in spawns
                    if enemy_type is KernelPanic
                ]

                if wave_number == len(WAVE_COMPOSITIONS):
                    self.assertEqual(bosses, [(KernelPanic, 1)])
                    self.assertEqual(spawns[0], (KernelPanic, 1))
                    self.assertTrue(any(
                        enemy_type is not KernelPanic
                        for enemy_type, level in spawns
                    ))
                else:
                    self.assertEqual(bosses, [])

    def test_enemy_types_spawn_in_round_robin_batches(self):
        """Interleave enemy batches in composition order."""
        for wave_number, composition in enumerate(WAVE_COMPOSITIONS, 1):
            with self.subTest(wave=wave_number):
                spawns = get_wave_spawns(wave_number)
                actual_order = [enemy_type for enemy_type, _ in spawns]
                remaining_counts = [count for _, count in composition]
                expected_order = []

                while any(remaining_counts):
                    for index, (enemy_type, _) in enumerate(composition):
                        batch_size = min(
                            remaining_counts[index], MAX_ENEMY_SPAWNING
                        )
                        expected_order.extend([enemy_type] * batch_size)
                        remaining_counts[index] -= batch_size

                self.assertEqual(actual_order, expected_order)

    def test_spawn_order_is_repeatable_and_presets_are_unchanged(self):
        """Build separate spawn lists without changing the presets."""
        original_compositions = tuple(
            tuple(composition) for composition in WAVE_COMPOSITIONS
        )

        for wave_number in range(1, len(WAVE_COMPOSITIONS) + 1):
            with self.subTest(wave=wave_number):
                first_spawns = get_wave_spawns(wave_number)
                repeated_spawns = get_wave_spawns(wave_number)

                self.assertEqual(first_spawns, repeated_spawns)
                self.assertIsNot(first_spawns, repeated_spawns)
                first_spawns.clear()
                self.assertEqual(
                    get_wave_spawns(wave_number), repeated_spawns
                )

        self.assertEqual(WAVE_COMPOSITIONS, original_compositions)

    def test_wave_numbers_outside_the_campaign_are_rejected(self):
        """Reject wave numbers before and after the preset campaign."""
        for wave_number in (0, len(WAVE_COMPOSITIONS) + 1):
            with self.subTest(wave=wave_number):
                with self.assertRaises(ValueError):
                    get_wave_spawns(wave_number)


if __name__ == "__main__":
    unittest.main()
