"""Share isolated Pygame sessions and identify the game under test."""

from contextlib import contextmanager, ExitStack
from dataclasses import asdict
from functools import lru_cache
import hashlib
import os
from pathlib import Path
from unittest.mock import patch

import pygame

from program_files.app import App
from program_files.screen.types.gameplay.enemy import LeakedFile
from program_files.screen.types.gameplay.enemy.wave_config import (
    WAVE_COMPOSITIONS,
)
from program_files.ui.sprite import Sprite
from program_files.ui.text_object import get_font


@contextmanager
def pygame_session(headless=False):
    """Clean up SDL, fonts, and frames after success or failure."""
    cached_frames = lru_cache(maxsize=None)(Sprite.get_frames)
    with ExitStack() as context:
        if headless:
            context.enter_context(patch.dict(os.environ, {
                "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy",
            }))
        context.enter_context(patch.object(
            Sprite, "get_frames", staticmethod(cached_frames),
        ))
        try:
            pygame.init()
            pygame.display.set_mode((App.DISPLAY_WIDTH, App.DISPLAY_HEIGHT))
            yield
        finally:
            cached_frames.cache_clear()
            get_font.cache_clear()
            pygame.quit()


def game_configuration(game):
    """Record live balance values and a fingerprint of game source."""
    source = Path(__file__).resolve().parents[1] / "program_files"
    digest = hashlib.sha256()
    for path in sorted(source.rglob("*.py")):
        digest.update(path.relative_to(source).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    enemy_types = dict.fromkeys(
        enemy_type for wave in WAVE_COMPOSITIONS for enemy_type, _ in wave
    )
    enemy_types[LeakedFile] = None
    return {
        "source_sha256": digest.hexdigest(),
        "pygame_version": pygame.version.ver,
        "max_waves": game.wave_state.MAX_WAVES,
        "start_money": game.START_MONEY,
        "max_health": game.MAX_HEALTH,
        "spawn_interval_ms": game.ENEMY_SPAWN_INTERVAL,
        "wave_reward_base": game.WAVE_CLEAR_REWARD_BASE,
        "wave_reward_per_wave": game.WAVE_CLEAR_REWARD_PER_WAVE,
        "tower_slots": len(game.tower_slots),
        "towers": {
            tower_type.__name__: {
                "cost": tower_type.COST,
                "levels": [asdict(level)
                           for level in tower_type.UPGRADE_LEVELS],
            }
            for tower_type in game.TOWER_SELECTION
        },
        "enemies": {
            enemy_type.__name__: [asdict(level)
                                  for level in enemy_type.LEVELS]
            for enemy_type in enemy_types
        },
        "waves": [
            {enemy_type.__name__: count for enemy_type, count in wave}
            for wave in WAVE_COMPOSITIONS
        ],
    }
