"""Compare planned Clock and Proxy purchases using normal game rules."""


# @generated fully ChatGPT 6.1 Sol: Tests

import argparse
from types import SimpleNamespace
from unittest.mock import patch
from program_files.screen.types.gameplay.gameplay import WaveState

from . import simulate_balance
from .simulate_balance import (
    ClockThrottler,
    FirewallPulse,
    NEON_GRID_MAP,
    ProxyBeam,
    TowerShop,
    get_wave_spawns,
)


class HybridShop(TowerShop):
    """Establish Firewalls, then finish each planned Clock or Proxy."""

    def __init__(
        self,
        game,
        strategy="hybrid",
        max_towers=None,
        starter_firewalls=1,
        proxy_after=3,
        proxy_every=0,
        switch_wave=7,
    ):
        """Store when to add the first Proxy and any later Proxies."""
        if (
            proxy_after < 0 or proxy_every < 0
            or not 1 <= switch_wave <= WaveState.MAX_WAVES
        ):
            raise ValueError("Proxy counts and switch wave must be valid.")
        if max_towers is None:
            max_towers = len(game.tower_slots)
        super().__init__(game, strategy, max_towers, starter_firewalls)
        self.proxy_after = proxy_after
        self.proxy_every = proxy_every
        self.switch_wave = switch_wave

    def allowed_types(self):
        """Use the normal Firewall purchase policy before switching."""
        return (FirewallPulse,)

    def next_tower_type(self):
        """Choose the next planned Clock or tank-focused Proxy."""
        clock_count = sum(
            isinstance(tower, ClockThrottler) for tower in self.game.towers
        )
        proxy_count = sum(
            isinstance(tower, ProxyBeam) for tower in self.game.towers
        )
        next_proxy = self.proxy_after + proxy_count * self.proxy_every
        if (
            (proxy_count == 0 or self.proxy_every > 0)
            and clock_count + proxy_count >= next_proxy
        ):
            return ProxyBeam
        return ClockThrottler

    def buy(self):
        """Finish each new tower before spending on another tower."""
        game = self.game
        if game.wave_state.round < self.switch_wave:
            return super().buy()

        roster = get_wave_spawns(game.wave_state.round)
        speed = sum(
            enemy_type.LEVELS[level - 1].speed
            for enemy_type, level in roster
        ) / len(roster)

        while True:
            upgrades = [
                tower for tower in game.towers
                if isinstance(tower, (ClockThrottler, ProxyBeam))
                and tower.can_upgrade
            ]
            if upgrades:
                tower = upgrades[-1]
                if game.money < tower.next_upgrade_cost:
                    return
                self.upgrade_tower(tower)
                continue

            slots = [slot for slot in game.tower_slots if not slot.occupied]
            if len(game.towers) >= self.max_towers or not slots:
                return
            tower_type = self.next_tower_type()
            if game.money < tower_type.COST:
                return

            load = [0.0] * len(self.samples)
            for tower in game.towers:
                covered, rate = self.performance(
                    type(tower), tower.tower_slot.rect.center,
                    tower.level, speed,
                )
                for index in covered:
                    load[index] += rate

            def value(slot):
                """Cover route sections with less existing damage."""
                covered, rate = self.performance(
                    tower_type, slot.rect.center,
                    len(tower_type.UPGRADE_LEVELS), speed,
                )
                return sum(
                    self.samples[index][2] * rate
                    / (1 + load[index] / 100)
                    for index in covered
                )

            self.place_tower(tower_type, max(slots, key=value))


def main():
    """Run one reproducible hybrid campaign with unchanged combat."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-after", type=int, default=3)
    parser.add_argument("--proxy-every", type=int, default=0)
    parser.add_argument("--switch-wave", type=int, default=7)
    parser.add_argument("--step-ms", type=int, default=17)
    parser.add_argument("--buy-during-wave", action="store_true")
    parser.add_argument("--max-seconds", type=int, default=10000)
    parser.add_argument(
        "--reserve-slots", type=int,
        default=len(NEON_GRID_MAP.tower_positions),
    )
    args = parser.parse_args()
    if (
        args.proxy_after < 0 or args.proxy_every < 0
        or not 1 <= args.switch_wave <= WaveState.MAX_WAVES
        or args.step_ms <= 0 or args.max_seconds <= 0 or args.reserve_slots < 0
    ):
        parser.error("Counts and durations must be within their valid ranges.")

    print(
        f"proxy_after={args.proxy_after} proxy_every={args.proxy_every} "
        f"switch_wave={args.switch_wave}", flush=True,
    )

    def make_shop(
        game,
        strategy,
        max_towers,
        starter_firewalls,
    ):
        """Use the requested hybrid plan in the shared simulation."""
        return HybridShop(
            game, strategy, max_towers, starter_firewalls,
            args.proxy_after, args.proxy_every, args.switch_wave,
        )

    campaign = SimpleNamespace(
        strategy="hybrid",
        step_ms=args.step_ms,
        reserve_slots=args.reserve_slots,
        max_seconds=args.max_seconds,
        buy_during_wave=args.buy_during_wave,
        starter_firewalls=1,
        enemy_health_scale=1,
        enemy_speed_scale=1,
        spawn_interval_ms=None,
    )
    with patch.object(simulate_balance, "TowerShop", make_shop):
        result = simulate_balance.simulate(campaign)
    if result["status"] == "timeout":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
