"""Record full campaigns, boss outcomes, and wave skipping."""


# @generated fully ChatGPT 6.1 Sol: Tests

import argparse
from contextlib import ExitStack
from functools import partial
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pygame

from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy import Enemy, KernelPanic
from program_files.screen.types.gameplay.gameplay import Gameplay, WaveState
from tools import simulate_balance as balance


class CampaignAudit:
    """Observe combat and rewards without changing their values."""

    def __init__(self, skip_waves=False):
        """Store the original methods and prepare result records."""
        self.skip_waves = skip_waves
        self.original_update = Gameplay.update
        self.original_damage = Enemy.take_damage
        self.game = None
        self.waves = []
        self.skips = []
        self.leaks = []
        self.recorded_waves = set()
        self.completed_waves = set()
        self.bosses = {}
        self.boss_records = {}
        self.kill_income = 0
        self.kills = 0
        self.peak_enemies = 0
        self.elapsed = 0

    def take_damage(self, enemy, damage):
        """Count normal kill rewards returned by the original method."""
        was_alive = enemy.is_alive
        reward = self.original_damage(enemy, damage)
        if was_alive and not enemy.is_alive and not enemy.reached_end:
            self.kill_income += reward
            self.kills += 1
        return reward

    def update(self, game, dt):
        """Record each real update and optionally press the skip key."""
        self.game = game
        before = tuple(game.enemy_state.enemies)
        self.original_update(game, dt)
        self.elapsed = pygame.time.get_ticks()
        self.peak_enemies = max(
            self.peak_enemies, len(game.enemy_state.enemies),
        )
        for enemy in before:
            if enemy.reached_end and not enemy.is_alive:
                self.leaks.append({
                    "enemy": type(enemy).__name__,
                    "wave": enemy.wave_number,
                    "health": enemy.health,
                    "seconds": self.elapsed / 1000,
                })

        for enemy in game.enemy_state.enemies:
            if isinstance(enemy, KernelPanic) and id(enemy) not in self.bosses:
                self.bosses[id(enemy)] = enemy
                self.boss_records[id(enemy)] = {
                    "spawn_seconds": self.elapsed / 1000,
                    "max_health": enemy.max_health,
                    "speed": enemy.speed,
                    "shield_activations": 0,
                    "shield_was_active": False,
                }
        for identity, boss in self.bosses.items():
            record = self.boss_records[identity]
            if boss.shield_active and not record["shield_was_active"]:
                record["shield_activations"] += 1
            record["shield_was_active"] = boss.shield_active
            if not boss.is_alive and "outcome" not in record:
                record.update({
                    "outcome": "escaped" if boss.reached_end else "killed",
                    "end_seconds": self.elapsed / 1000,
                    "remaining_health": boss.health,
                    "distance_to_finish": boss.distance_to_finish,
                })

        if self.skip_waves and game.can_skip_wave:
            wave = game.wave_state.round
            game.handle_event(pygame.event.Event(
                pygame.KEYDOWN, key=pygame.K_s,
            ))
            self.skips.append({
                "from_wave": wave,
                "to_wave": game.wave_state.round,
                "seconds": self.elapsed / 1000,
            })

        for wave in sorted(game.wave_state.rewarded_waves):
            if wave not in self.recorded_waves:
                self.recorded_waves.add(wave)
                self.waves.append({
                    "wave": wave,
                    "health": game.health,
                    "money": game.money,
                    "towers": len(game.towers),
                    "seconds": self.elapsed / 1000,
                })
        self.completed_waves.update(
            self.recorded_waves - game.wave_state.active_waves
        )

    def result(self, args, simulation):
        """Summarize victory, spending, leaks, and boss outcomes."""
        game = self.game
        build = [{
            "tower": type(tower).__name__,
            "level": tower.level,
            "slot": list(tower.tower_slot.rect.topleft),
            "total_cost": tower.total_cost,
        } for tower in game.towers]
        spent = sum(tower.total_cost for tower in game.towers)
        wave_income = sum(
            game.WAVE_CLEAR_REWARD_BASE
            + wave * game.WAVE_CLEAR_REWARD_PER_WAVE
            for wave in self.recorded_waves
        )
        expected_money = (
            game.START_MONEY + self.kill_income + wave_income - spent
        )
        boss_results = []
        for identity, record in self.boss_records.items():
            boss = self.bosses[identity]
            boss_results.append({
                key: value for key, value in record.items()
                if key != "shield_was_active"
            })
            boss_results[-1].setdefault("outcome", "alive_at_end")
            boss_results[-1].setdefault("remaining_health", boss.health)
            boss_results[-1].setdefault(
                "distance_to_finish", boss.distance_to_finish,
            )
        return {
            "strategy": args.strategy,
            "clock_wave": args.clock_wave,
            "clock_level": args.clock_level,
            "proxy_after": args.proxy_after,
            "proxy_every": args.proxy_every,
            "step_ms": args.step_ms,
            "skip_waves": args.skip_waves,
            "status": simulation["status"],
            "configuration": simulation["configuration"],
            "waves_cleared": len(self.completed_waves),
            "waves_rewarded": len(self.recorded_waves),
            "last_wave_started": game.wave_state.round,
            "health": game.health,
            "money": game.money,
            "game_seconds": self.elapsed / 1000,
            "peak_enemies": self.peak_enemies,
            "bosses": boss_results,
            "kills": self.kills,
            "kill_income": self.kill_income,
            "wave_income": wave_income,
            "spent": spent,
            "money_accounting_valid": expected_money == game.money,
            "build": build,
            "waves": self.waves,
            "skips": self.skips,
            "leaks": self.leaks,
        }


def main():
    """Run a normal campaign and save a complete audit as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strategy", default="mixed-upgrades", choices=balance.STRATEGIES,
    )
    parser.add_argument("--step-ms", type=int, default=17)
    parser.add_argument("--max-seconds", type=int, default=10000)
    parser.add_argument("--clock-wave", type=int)
    parser.add_argument("--clock-level", type=int, default=2)
    parser.add_argument("--proxy-after", type=int)
    parser.add_argument("--proxy-every", type=int, default=0)
    parser.add_argument("--skip-waves", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if (
        args.step_ms <= 0 or args.max_seconds <= 0
        or not 1 <= args.clock_level <= len(
            balance.ClockThrottler.UPGRADE_LEVELS
        )
    ):
        parser.error("Use positive timing and an available Clock level.")
    if (
        args.clock_wave is not None
        and not 1 <= args.clock_wave <= WaveState.MAX_WAVES
    ):
        parser.error(
            f"The Clock starting wave must be from 1 to {WaveState.MAX_WAVES}."
        )
    if args.proxy_after is not None and args.proxy_after < 0:
        parser.error("The number of Clocks before a Proxy must be positive.")
    if args.proxy_every < 0:
        parser.error("The Proxy interval must be zero or positive.")
    settings = SimpleNamespace(
        strategy=args.strategy, step_ms=args.step_ms,
        buy_during_wave=True, starter_firewalls=1,
        reserve_slots=len(NEON_GRID_MAP.tower_positions),
        max_seconds=args.max_seconds, enemy_health_scale=1,
        enemy_speed_scale=1, spawn_interval_ms=None,
    )
    audit = CampaignAudit(args.skip_waves)

    def observe_update(game, dt):
        """Keep the normal method binding while recording updates."""
        audit.update(game, dt)

    def observe_damage(enemy, damage):
        """Keep the normal method binding while recording rewards."""
        return audit.take_damage(enemy, damage)

    with ExitStack() as context:
        if args.proxy_after is not None:
            from tools.compare_hybrids import HybridShop

            context.enter_context(patch.object(
                balance, "TowerShop", partial(
                    HybridShop, switch_wave=args.clock_wave or 7,
                    proxy_after=args.proxy_after,
                    proxy_every=args.proxy_every,
                ),
            ))
        elif args.clock_wave is not None:
            from tools.compare_builds import ClockTierShop

            context.enter_context(patch.object(
                balance, "TowerShop", partial(
                    ClockTierShop, switch_wave=args.clock_wave,
                    clock_level=args.clock_level,
                ),
            ))
        context.enter_context(patch.object(Gameplay, "update", observe_update))
        context.enter_context(patch.object(
            Enemy, "take_damage", observe_damage,
        ))
        simulation = balance.simulate(settings)
    result = audit.result(args, simulation)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        key: value for key, value in result.items()
        if key not in ("build", "waves", "leaks", "skips", "configuration")
    }))
    if result["status"] == "timeout":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
