"""Compare buyer estimates without changing actual tower damage."""



# @generated fully ChatGPT 6.1 Sol: Tests

import argparse
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.simulate_balance import (  # noqa: E402
    ClockThrottler,
    NEON_GRID_MAP,
    TowerShop,
    simulate,
)


def main():
    """Temporarily favor Clock estimates during a normal campaign."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("factor", type=float, choices=(1.5, 2, 3, 5))
    args = parser.parse_args()
    original_performance = TowerShop.performance

    def weighted_performance(
        shop,
        tower_type,
        center,
        level,
        speed,
    ):
        """Change only the damage rate used to compare purchases."""
        covered, rate = original_performance(
            shop, tower_type, center, level, speed,
        )
        if tower_type is ClockThrottler:
            rate *= args.factor
        return covered, rate

    print(f"AoE buyer estimate multiplier={args.factor:g}", flush=True)
    campaign = SimpleNamespace(
        strategy="efficient",
        step_ms=17,
        reserve_slots=len(NEON_GRID_MAP.tower_positions),
        max_seconds=10000,
        buy_during_wave=True,
        starter_firewalls=1,
        enemy_health_scale=1,
        enemy_speed_scale=1,
        spawn_interval_ms=None,
    )
    with patch.object(TowerShop, "performance", weighted_performance):
        simulate(campaign)


if __name__ == "__main__":
    main()
