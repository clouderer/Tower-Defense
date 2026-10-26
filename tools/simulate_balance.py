"""Run repeatable campaigns through the game's actual update methods."""


# @generated fully ChatGPT 6.1 Sol: Tests

import argparse
from contextlib import ExitStack
from dataclasses import replace
from functools import lru_cache
import json
import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pygame

from program_files.maps.game_map import NEON_GRID_MAP
from program_files.screen.types.gameplay.enemy import (
    Glitchworm,
    KernelPanic,
    LeakedFile,
    PingFlooder,
    Ransomware,
    TrojanFile,
)
from program_files.screen.types.gameplay.enemy.wave_config import (
    get_wave_spawns, WAVE_COMPOSITIONS,
)
from program_files.screen.types.gameplay.gameplay import Gameplay
from program_files.screen.types.gameplay.tower.bitblaster import BitBlaster
from program_files.screen.types.gameplay.tower.clock_throttler import (
    ClockThrottler,
)
from program_files.screen.types.gameplay.tower.firewall_pulse import (
    FirewallPulse,
)
from program_files.screen.types.gameplay.tower.proxy_beam import ProxyBeam
from tools.runtime import game_configuration, pygame_session


TOWER_TYPES = tuple(Gameplay.TOWER_SELECTION)
ENEMY_TYPES = tuple(dict.fromkeys(
    [enemy_type for wave in WAVE_COMPOSITIONS for enemy_type, _ in wave]
    + [LeakedFile]
))
STRATEGIES = (
    "efficient", "firewall", "bitblaster", "no-upgrades",
    "clock-heavy", "upgrade-focused", "mixed-upgrades",
)


def route_samples(
    path,
):
    """Sample the full route at roughly four-pixel intervals."""
    samples = []
    for start, end in zip(path, path[1:]):
        length = math.dist(start, end)
        count = max(1, math.ceil(length / 4))
        for index in range(count):
            fraction = (index + 0.5) / count
            samples.append((
                start[0] + (end[0] - start[0]) * fraction,
                start[1] + (end[1] - start[1]) * fraction,
                length / count,
            ))
    return tuple(samples)


class TowerShop:
    """Buy towers using damage, route coverage, and cost."""

    def __init__(
        self,
        game,
        strategy,
        max_towers,
        starter_firewalls=1,
    ):
        """Store the build policy and sample the map's route."""
        self.game = game
        self.strategy = strategy
        self.max_towers = max_towers
        self.starter_firewalls = starter_firewalls
        self.samples = route_samples(game.game_map.enemy_path)
        self.tower_offsets = {}

    @lru_cache(maxsize=None)
    def coverage(
        self,
        tower_type,
        center,
        level,
    ):
        """Find route samples covered by this tower and level."""
        radius = tower_type.UPGRADE_LEVELS[level - 1].range
        if tower_type not in self.tower_offsets:
            slot = self.game.tower_slots[0]
            tower = tower_type(slot)
            self.tower_offsets[tower_type] = (
                tower.rect.centerx - slot.rect.centerx,
                tower.rect.centery - slot.rect.centery,
            )
        offset_x, offset_y = self.tower_offsets[tower_type]
        position = (center[0] + offset_x, center[1] + offset_y)
        return tuple(
            index for index, sample in enumerate(self.samples)
            if math.dist(position, sample[:2]) <= radius
        )

    def performance(
        self,
        tower_type,
        center,
        level,
        speed,
    ):
        """Estimate damage across all covered route samples."""
        stats = tower_type.UPGRADE_LEVELS[level - 1]
        covered = self.coverage(tower_type, center, level)
        damage_rate = stats.damage * 1000 / stats.attack_cooldown
        if tower_type is ClockThrottler:
            route_length = sum(self.samples[index][2] for index in covered)
            interval = self.game.ENEMY_SPAWN_INTERVAL / 1000
            targets = route_length / max(speed * interval, 1)
            damage_rate *= min(12, max(1, targets))
        return covered, damage_rate

    def allowed_types(self):
        """Choose the tower types allowed by the selected policy."""
        if self.strategy in ("firewall", "mixed-upgrades"):
            return (FirewallPulse,)
        if self.strategy == "bitblaster":
            return (BitBlaster,)
        if self.strategy == "clock-heavy":
            has_clock = any(
                isinstance(tower, ClockThrottler)
                for tower in self.game.towers
            )
            if self.game.wave_state.round < 3 and not has_clock:
                return (FirewallPulse,)
            return (ClockThrottler,)
        return TOWER_TYPES

    def buy(self):
        """Spend available money on the strongest affordable changes."""
        if self.strategy == "upgrade-focused":
            self.buy_focused()
            return
        if (
            self.strategy == "mixed-upgrades"
            and self.game.wave_state.round >= 10
        ):
            self.buy_focused(clock_only=True)
            return

        game = self.game
        roster = get_wave_spawns(game.wave_state.round)
        speed = sum(
            enemy_type.LEVELS[level - 1].speed
            for enemy_type, level in roster
        ) / len(roster)

        while True:
            candidates = []
            load = [0.0] * len(self.samples)
            for tower in game.towers:
                covered, rate = self.performance(
                    type(tower), tower.tower_slot.rect.center,
                    tower.level, speed,
                )
                for index in covered:
                    load[index] += rate

            def value(covered, rate):
                """Favor route parts with less existing damage."""
                return sum(
                    self.samples[index][2] * rate
                    / (1 + load[index] / 100)
                    for index in covered
                )

            if len(game.towers) < self.max_towers:
                for slot in game.tower_slots:
                    if slot.occupied:
                        continue
                    for tower_type in self.allowed_types():
                        if game.money < tower_type.COST:
                            continue
                        covered, rate = self.performance(
                            tower_type, slot.rect.center, 1, speed,
                        )
                        score = value(covered, rate) / tower_type.COST
                        candidates.append((score, "build", tower_type, slot))

            if self.strategy != "no-upgrades":
                for tower in game.towers:
                    cost = tower.next_upgrade_cost
                    if cost is None or game.money < cost:
                        continue
                    center = tower.tower_slot.rect.center
                    covered, rate = self.performance(
                        type(tower), center, tower.level, speed,
                    )
                    new_covered, new_rate = self.performance(
                        type(tower), center, tower.level + 1, speed,
                    )
                    gain = value(new_covered, new_rate) - value(covered, rate)
                    candidates.append((gain / cost, "upgrade", tower, None))

            if not candidates:
                break

            score, action, item, slot = max(candidates, key=lambda row: row[0])
            if score <= 0:
                break
            if action == "build":
                self.place_tower(item, slot)
            else:
                self.upgrade_tower(item)

    def place_tower(self, tower_type, slot):
        """Pay for a tower and add it to the selected slot."""
        self.game.money -= tower_type.COST
        slot.occupied = True
        self.game.towers.append(tower_type(slot))

    def upgrade_tower(self, tower):
        """Select a tower and pay for its next upgrade."""
        self.game.sidebar_tower = tower
        self.game.upgrade_tower()
        self.game.sidebar_tower = None

    def buy_focused(self, clock_only=False):
        """Upgrade each new Clock after any starting Firewalls."""
        game = self.game
        roster = get_wave_spawns(game.wave_state.round)
        speed = sum(
            enemy_type.LEVELS[level - 1].speed
            for enemy_type, level in roster
        ) / len(roster)
        while True:
            upgrades = [
                tower for tower in game.towers
                if tower.can_upgrade and (
                    not clock_only or isinstance(tower, ClockThrottler)
                )
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
            firewall_count = sum(
                isinstance(tower, FirewallPulse) for tower in game.towers
            )
            tower_type = (
                FirewallPulse if (
                    not clock_only
                    and firewall_count < self.starter_firewalls
                )
                else ClockThrottler
            )
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
                """Choose a slot for the tower's final range."""
                covered, rate = self.performance(
                    tower_type, slot.rect.center,
                    len(tower_type.UPGRADE_LEVELS), speed,
                )
                return sum(
                    self.samples[index][2] * rate
                    / (1 + load[index] / 100)
                    for index in covered
                )

            slot = max(slots, key=value)
            self.place_tower(tower_type, slot)


def simulate(args):
    """Run the actual game updates with a deterministic clock."""
    app = SimpleNamespace(
        get_main_menu=lambda: None,
        get_settings=lambda: None,
        change_screen=lambda screen: None,
    )
    elapsed = 0
    max_enemies = 0
    completed_waves = set()
    print(
        f"strategy={args.strategy} step_ms={args.step_ms} "
        f"during_wave={args.buy_during_wave} max_towers={args.reserve_slots}"
    )
    if args.strategy == "upgrade-focused":
        print(f"starter_firewalls={args.starter_firewalls}")
    with (
        pygame_session(headless=True),
        ExitStack() as overrides,
        patch.object(pygame.time, "get_ticks", lambda: elapsed),
    ):
        apply_overrides(args, overrides)
        game = Gameplay(app, NEON_GRID_MAP)
        configuration = game_configuration(game)
        print(f"game_source_sha256={configuration['source_sha256']}")
        print("wave  health  money  towers  upgrades  seconds  status")
        shop = TowerShop(
            game, args.strategy, args.reserve_slots, args.starter_firewalls,
        )
        last_purchase = 0
        while not game.game_over and not game.wave_state.won:
            if elapsed >= args.max_seconds * 1000:
                break
            if game.wave_state.next_ready:
                shop.buy()
                game.start_wave()
            elif (
                args.buy_during_wave and game.wave_state.active
                and elapsed - last_purchase >= 1000
            ):
                shop.buy()
                last_purchase = elapsed

            step_ms = min(args.step_ms, args.max_seconds * 1000 - elapsed)
            elapsed += step_ms
            game.update(step_ms / 1000)
            max_enemies = max(max_enemies, len(game.enemy_state.enemies))
            finished = (
                game.wave_state.rewarded_waves - game.wave_state.active_waves
            )
            for wave in sorted(finished - completed_waves):
                if wave % 5 == 0:
                    print_checkpoint(game, elapsed, "cleared", wave=wave)
            completed_waves.update(finished)
            if game.game_over:
                print_checkpoint(game, elapsed, "defeat")

        status = "victory" if game.wave_state.won else (
            "defeat" if game.game_over else "timeout"
        )
        result = {
            "status": status,
            "waves_cleared": len(completed_waves),
            "last_wave_started": game.wave_state.round,
            "health": game.health,
            "money": game.money,
            "max_enemies": max_enemies,
            "game_seconds": elapsed / 1000,
            "configuration": configuration,
            "settings": vars(args).copy(),
        }
        print(
            f"result={status} cleared={len(completed_waves)}/"
            f"{game.wave_state.MAX_WAVES} hp={game.health} "
            f"money={game.money} max_enemies={max_enemies} "
            f"seconds={elapsed / 1000:.1f}"
        )
        print_build(game)
        return result


def apply_overrides(
    args,
    overrides,
):
    """Temporarily scale enemy stats and change the spawn interval."""
    for enemy_type in ENEMY_TYPES:
        levels = tuple(
            replace(
                stats,
                health=(stats.health if args.enemy_health_scale == 1 else
                        max(1, round(stats.health * args.enemy_health_scale))),
                speed=stats.speed * args.enemy_speed_scale,
            )
            for stats in enemy_type.LEVELS
        )
        overrides.enter_context(patch.object(enemy_type, "LEVELS", levels))
    if args.spawn_interval_ms is not None:
        overrides.enter_context(patch.object(
            Gameplay, "ENEMY_SPAWN_INTERVAL", args.spawn_interval_ms,
        ))
    print(
        f"enemy_health_scale={args.enemy_health_scale:g} "
        f"enemy_speed_scale={args.enemy_speed_scale:g} "
        f"spawn_interval_ms={Gameplay.ENEMY_SPAWN_INTERVAL}"
    )
    if args.enemy_health_scale != 1 or args.enemy_speed_scale != 1:
        for enemy_type in ENEMY_TYPES:
            health = "/".join(str(stats.health) for stats in enemy_type.LEVELS)
            speed = "/".join(
                f"{stats.speed:g}" for stats in enemy_type.LEVELS
            )
            print(f"{enemy_type.__name__}: health={health} speed={speed}")


def print_checkpoint(game, elapsed, status, wave=None):
    """Show health, spending, and elapsed game time at a checkpoint."""
    upgrades = sum(tower.level - 1 for tower in game.towers)
    wave = game.wave_state.round if wave is None else wave
    print(
        f"{wave:4d}  {game.health:6g}  {game.money:5d}  "
        f"{len(game.towers):6d}  {upgrades:8d}  "
        f"{elapsed / 1000:7.1f}  {status}",
        flush=True,
    )


def print_build(game):
    """Show the final number of each tower type at every level."""
    build = []
    for tower_type in TOWER_TYPES:
        levels = []
        for level in range(1, len(tower_type.UPGRADE_LEVELS) + 1):
            count = sum(
                type(tower) is tower_type and tower.level == level
                for tower in game.towers
            )
            if count:
                levels.append(f"L{level}x{count}")
        if levels:
            build.append(f"{tower_type.__name__}:{','.join(levels)}")
    print("build=" + " ".join(build))


def main():
    """Read the campaign policy and run one simulation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strategy", default="efficient",
        choices=STRATEGIES,
    )
    parser.add_argument("--buy-during-wave", action="store_true")
    parser.add_argument(
        "--starter-firewalls", type=int, default=1,
        help="Starting Firewalls for the upgrade-focused strategy.",
    )
    parser.add_argument(
        "--reserve-slots", type=int,
        default=len(NEON_GRID_MAP.tower_positions),
        help="Maximum tower count, for comparing restricted defenses.",
    )
    parser.add_argument("--step-ms", type=int, default=20)
    parser.add_argument("--max-seconds", type=int, default=10000)
    parser.add_argument(
        "--output", help="Save the result and live config as JSON.")
    parser.add_argument(
        "--enemy-health-scale", type=float, default=1,
        help="Multiply all enemy health, including spawnlings, for this run.",
    )
    parser.add_argument(
        "--enemy-speed-scale", type=float, default=1,
        help="Multiply all enemy speeds, including spawnlings, for this run.",
    )
    parser.add_argument(
        "--spawn-interval-ms", type=int,
        help="Override regular enemy spawn spacing for this run.",
    )
    args = parser.parse_args()
    if args.step_ms <= 0 or args.max_seconds <= 0 or args.reserve_slots < 0:
        parser.error("Step duration must be positive and tower limit valid.")
    if args.starter_firewalls <= 0:
        parser.error("The number of starting Firewalls must be positive.")
    for scale in (args.enemy_health_scale, args.enemy_speed_scale):
        if not math.isfinite(scale) or scale <= 0:
            parser.error("Enemy stat scales must be positive finite numbers.")
    if args.spawn_interval_ms is not None and args.spawn_interval_ms <= 0:
        parser.error("Spawn interval must be positive.")
    result = simulate(args)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) +
                          "\n", encoding="utf-8")
    if result["status"] == "timeout":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
