"""Test a recorded, prebuilt defense against the current boss alone."""



# @generated fully ChatGPT 6.1 Sol: Tests

from collections import Counter
from functools import lru_cache
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RESULT_DIRECTORY = Path(__file__).resolve().parent
SOURCE_SUMMARY = (
    PROJECT_ROOT / "tools/balance_results/visible_good/summary.json"
)





def run_isolated(
    step_ms,
    recorded_build,
    cached_frames,
):
    """Supply the recorded defense without simulating its funding."""
    from program_files.maps.game_map import NEON_GRID_MAP
    from program_files.screen.types.gameplay.enemy import KernelPanic
    from program_files.screen.types.gameplay.gameplay import Gameplay
    from program_files.screen.types.gameplay.tower.bitblaster import (
        BitBlaster,
    )
    from program_files.screen.types.gameplay.tower.clock_throttler import (
        ClockThrottler,
    )
    from program_files.screen.types.gameplay.tower.firewall_pulse import (
        FirewallPulse,
    )
    from program_files.screen.types.gameplay.tower.proxy_beam import ProxyBeam
    from program_files.ui.sprite import Sprite

    tower_types = {
        tower_type.__name__: tower_type for tower_type in (
            FirewallPulse, BitBlaster, ProxyBeam, ClockThrottler,
        )
    }
    elapsed = 0
    real_start = time.perf_counter()
    app = SimpleNamespace(
        get_main_menu=lambda: None,
        get_settings=lambda: None,
        change_screen=lambda screen: None,
    )

    with (
        patch.object(pygame.time, "get_ticks", lambda: elapsed),
        patch.object(Sprite, "get_frames", staticmethod(cached_frames)),
    ):
        game = Gameplay(app, NEON_GRID_MAP)
        slots = {
            (slot.x_pos, slot.y_pos): slot for slot in game.tower_slots
        }
        defense_cost = 0
        verified_build = []
        for entry in recorded_build:
            tower_type = tower_types[entry["tower"]]
            slot = slots[tuple(entry["slot"])]
            if slot.occupied:
                raise ValueError("The recorded defense repeats a tower slot.")
            tower = tower_type(slot)
            while tower.level < entry["level"]:
                cost = tower.next_upgrade_cost
                if cost is None or not tower.upgrade():
                    raise ValueError("The recorded tower level is invalid.")
                tower.total_cost += cost
            if tower.total_cost != entry["total_cost"]:
                raise ValueError("Current prices differ from the recording.")
            slot.occupied = True
            game.towers.append(tower)
            defense_cost += tower.total_cost
            verified_build.append({
                "tower": type(tower).__name__,
                "level": tower.level,
                "slot": list(entry["slot"]),
                "current_total_cost": tower.total_cost,
            })

        boss = KernelPanic(game.game_map.enemy_path)
        boss.wave_number = 25
        game.enemy_state.enemies = [boss]
        game.wave_state.round = 25
        game.wave_state.active = True
        game.wave_state.next_ready = False
        game.wave_state.active_waves = {25}
        initial_player_health = game.health
        initial_player_money = game.money
        shield_phases = []
        shield_seconds = 0.0
        snapshots = []
        next_snapshot = 30000

        while boss.is_alive and not boss.reached_end and not game.game_over:
            if elapsed > 600000:
                raise RuntimeError("The isolated boss fight timed out.")
            shield_before = boss.shield_active
            elapsed += step_ms
            game.update(step_ms / 1000)
            shield_after = boss.shield_active
            if shield_after:
                shield_seconds += step_ms / 1000
            if shield_after and not shield_before:
                shield_phases.append({
                    "start_seconds": round(elapsed / 1000, 3),
                    "end_seconds": None,
                })
            elif shield_before and not shield_after and shield_phases:
                shield_phases[-1]["end_seconds"] = round(elapsed / 1000, 3)
            if elapsed >= next_snapshot:
                snapshots.append({
                    "seconds": round(elapsed / 1000, 3),
                    "boss_health": boss.health,
                    "remaining_path_distance": boss.distance_to_finish,
                })
                next_snapshot += 30000

        killed = not boss.is_alive and not boss.reached_end
        escaped = boss.reached_end
        build_counts = Counter(
            f"{type(tower).__name__} L{tower.level}" for tower in game.towers
        )
        result = {
            "test_scope": "isolated boss against a prebuilt defense",
            "funding_path_tested": False,
            "full_campaign_tested": False,
            "ordinary_wave_25_enemies_present": False,
            "step_ms": step_ms,
            "video_driver": pygame.display.get_driver(),
            "defense_cost": defense_cost,
            "recorded_defense_cost": sum(
                entry["total_cost"] for entry in recorded_build
            ),
            "defense_counts": dict(build_counts),
            "tower_count": len(game.towers),
            "initial_player_health": initial_player_health,
            "initial_player_money": initial_player_money,
            "ending_player_health": game.health,
            "ending_player_money": game.money,
            "boss_max_health": boss.max_health,
            "boss_speed": boss.speed,
            "shield_interval": boss.SHIELD_INTERVAL,
            "shield_duration": boss.SHIELD_DURATION,
            "shield_damage_multiplier": boss.SHIELD_DAMAGE_MULTIPLIER,
            "boss_health_end": boss.health,
            "boss_damage_taken": boss.max_health - boss.health,
            "remaining_path_distance": boss.distance_to_finish,
            "boss_position_end": [boss.x_position, boss.y_position],
            "killed": killed,
            "escaped": escaped,
            "boss_fight_seconds": round(elapsed / 1000, 3),
            "shield_phases_started": len(shield_phases),
            "observed_shield_seconds": round(shield_seconds, 3),
            "shield_phases": shield_phases,
            "health_snapshots": snapshots,
            "game_over": game.game_over,
            "real_seconds": round(time.perf_counter() - real_start, 3),
            "verified_build": verified_build,
        }
        print(json.dumps({
            key: value for key, value in result.items()
            if key not in (
                "shield_phases", "health_snapshots", "verified_build",
            )
        }), flush=True)
        return result


def main():
    """Save isolated boss results at three normal frame durations."""
    sys.path.insert(0, str(PROJECT_ROOT))
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((600, 350))

    from program_files.ui.sprite import Sprite
    from program_files.ui.text_object import get_font

    recorded_build = json.loads(SOURCE_SUMMARY.read_text())["build"]
    cached_frames = lru_cache(maxsize=None)(Sprite.get_frames)
    try:
        runs = [
            run_isolated(step_ms, recorded_build, cached_frames)
            for step_ms in (17, 20, 33)
        ]
        result = {
            "source_defense_summary": str(
                SOURCE_SUMMARY.relative_to(PROJECT_ROOT)
            ),
            "scope": (
                "This supplies the recorded defense before the boss arrives. "
                "It does not simulate earning its cost or surviving waves "
                "1-24, and it omits the ordinary enemies in wave 25."
            ),
            "production_stats_modified": False,
            "runs": runs,
        }
        output = RESULT_DIRECTORY / "boss_isolated.json"
        output.write_text(json.dumps(result, indent=2) + "\n")
        print(f"Saved {output}")
    finally:
        cached_frames.cache_clear()
        get_font.cache_clear()
        pygame.quit()


if __name__ == "__main__":
    main()
