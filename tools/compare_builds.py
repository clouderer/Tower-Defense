"""Compare affordable Clock builds through the actual game updates."""


# @generated fully ChatGPT 6.1 Sol: Tests

import argparse
from functools import partial
import math
import sys
from unittest.mock import patch

from . import simulate_balance
from .simulate_balance import ClockThrottler, FirewallPulse, TowerShop
from program_files.screen.types.gameplay.gameplay import WaveState


class ClockTierShop(TowerShop):
    """Build Firewalls first, then add Clocks at the selected level."""

    def __init__(
        self,
        game,
        strategy,
        max_towers,
        starter_firewalls=1,
        switch_wave=7,
        clock_level=2,
        finish_firewalls=False,
        coverage_bias=100,
    ):
        """Store when to switch and which Clock level to build first."""
        super().__init__(game, strategy, max_towers, starter_firewalls)
        if not 1 <= switch_wave <= WaveState.MAX_WAVES:
            raise ValueError("The switch wave must belong to the campaign.")
        if not 1 <= clock_level <= len(ClockThrottler.UPGRADE_LEVELS):
            raise ValueError("The Clock level must exist in UPGRADE_LEVELS.")
        if coverage_bias is not None and (
            not math.isfinite(coverage_bias) or coverage_bias <= 0
        ):
            raise ValueError("Coverage bias must be positive or None.")
        self.switch_wave = switch_wave
        self.clock_level = clock_level
        self.finish_firewalls = finish_firewalls
        self.coverage_bias = coverage_bias

    def buy(self):
        """Build Clocks before buying their final upgrades."""
        if self.game.wave_state.round < self.switch_wave:
            previous_strategy = self.strategy
            self.strategy = "firewall"
            try:
                super().buy()
            finally:
                self.strategy = previous_strategy
            return

        game = self.game
        if self.finish_firewalls:
            for tower in game.towers:
                if isinstance(tower, FirewallPulse) and tower.level == 1:
                    if game.money < tower.next_upgrade_cost:
                        return
                    self.upgrade_tower(tower)
        roster = simulate_balance.get_wave_spawns(game.wave_state.round)
        speed = sum(
            enemy_type.LEVELS[level - 1].speed
            for enemy_type, level in roster
        ) / len(roster)

        while True:
            slots = [slot for slot in game.tower_slots if not slot.occupied]
            full = len(game.towers) >= self.max_towers or not slots
            target_level = (
                len(ClockThrottler.UPGRADE_LEVELS) if full
                else self.clock_level
            )
            upgrades = [
                tower for tower in game.towers
                if isinstance(tower, ClockThrottler)
                and tower.level < target_level and tower.can_upgrade
            ]
            if upgrades:
                tower = upgrades[-1]
                if game.money < tower.next_upgrade_cost:
                    return
                self.upgrade_tower(tower)
                continue

            if full or game.money < ClockThrottler.COST:
                return

            load = [0.0] * len(self.samples)
            for tower in game.towers:
                covered, rate = self.performance(
                    type(tower), tower.tower_slot.rect.center,
                    tower.level, speed,
                )
                for index in covered:
                    load[index] += rate

            def score(slot):
                """Choose a slot using the intended Clock level."""
                covered, rate = self.performance(
                    ClockThrottler, slot.rect.center,
                    self.clock_level, speed,
                )
                return sum(
                    self.samples[index][2] * rate
                    / (
                        1 + load[index] / self.coverage_bias
                        if self.coverage_bias is not None else 1
                    )
                    for index in covered
                )

            self.place_tower(ClockThrottler, max(slots, key=score))


def main():
    """Run a complete campaign with the selected Clock build policy."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--switch-wave", type=int, default=7)
    parser.add_argument(
        "--clock-level", type=int,
        choices=range(1, len(ClockThrottler.UPGRADE_LEVELS) + 1), default=2,
    )
    parser.add_argument("--step-ms", type=int, default=17)
    parser.add_argument("--finish-firewalls", action="store_true")
    parser.add_argument("--coverage-bias", default="100")
    args = parser.parse_args()
    if not 1 <= args.switch_wave <= WaveState.MAX_WAVES or args.step_ms <= 0:
        parser.error("Use a campaign wave and a positive frame duration.")
    try:
        coverage_bias = (
            None if args.coverage_bias.lower() == "none"
            else float(args.coverage_bias)
        )
    except ValueError:
        parser.error("Coverage bias must be a number or 'none'.")
    if coverage_bias is not None and (
        not math.isfinite(coverage_bias) or coverage_bias <= 0
    ):
        parser.error("Coverage bias must be positive.")

    shop = partial(
        ClockTierShop, switch_wave=args.switch_wave,
        clock_level=args.clock_level, finish_firewalls=args.finish_firewalls,
        coverage_bias=coverage_bias,
    )
    argv = [
        "simulate_balance", "--strategy", "mixed-upgrades",
        "--buy-during-wave", "--step-ms", str(args.step_ms),
    ]
    print(
        f"clock_transition_wave={args.switch_wave} "
        f"initial_clock_level={args.clock_level} "
        f"finish_firewalls={args.finish_firewalls} "
        f"coverage_bias={coverage_bias}"
    )
    with (
        patch.object(simulate_balance, "TowerShop", shop),
        patch.object(sys, "argv", argv),
    ):
        simulate_balance.main()


if __name__ == "__main__":
    main()
