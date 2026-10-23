"""Set up enemy groups and levels for each wave."""

from .enemy import Enemy
from .glitchworm import Glitchworm
from .kernel_panic import KernelPanic
from .ping_flooder import PingFlooder
from .ransomware import Ransomware
from .trojan_file import TrojanFile


WAVES_PER_ENEMY_LEVEL = 3
MAX_ENEMY_LEVEL = 8
MAX_ENEMY_SPAWNING = 5


# Each wave lists the enemy classes and how many enemies to spawn.
# Trojan Files create additional spawnlings during the wave.
WAVE_COMPOSITIONS: tuple[tuple[tuple[type[Enemy], int], ...], ...] = (
    ((Glitchworm, 2),),
    ((Glitchworm, 3),),
    ((PingFlooder, 2), (Glitchworm, 4)),
    ((PingFlooder, 2), (Glitchworm, 3)),
    ((PingFlooder, 3), (Glitchworm, 4)),
    ((PingFlooder, 8), (Glitchworm, 10)),
    ((PingFlooder, 12), (Glitchworm, 14), (Ransomware, 1)),
    ((PingFlooder, 16), (Glitchworm, 18), (Ransomware, 1), (TrojanFile, 1)),
    ((PingFlooder, 20), (Glitchworm, 22), (Ransomware, 2), (TrojanFile, 1)),
    ((PingFlooder, 24), (Glitchworm, 26), (Ransomware, 3), (TrojanFile, 2)),
    ((PingFlooder, 28), (Glitchworm, 30), (Ransomware, 4), (TrojanFile, 3)),
    ((PingFlooder, 32), (Glitchworm, 32), (Ransomware, 5), (TrojanFile, 4)),
    ((PingFlooder, 34), (Glitchworm, 34), (Ransomware, 5), (TrojanFile, 5)),
    ((PingFlooder, 36), (Glitchworm, 36), (Ransomware, 6), (TrojanFile, 5)),
    ((PingFlooder, 40), (Glitchworm, 38), (Ransomware, 6), (TrojanFile, 5)),
    ((PingFlooder, 40), (Glitchworm, 36), (Ransomware, 7), (TrojanFile, 6)),
    ((PingFlooder, 42), (Glitchworm, 38), (Ransomware, 8), (TrojanFile, 6)),
    ((PingFlooder, 46), (Glitchworm, 40), (Ransomware, 9), (TrojanFile, 7)),
    ((PingFlooder, 50), (Glitchworm, 42), (Ransomware, 10), (TrojanFile, 7)),
    ((PingFlooder, 54), (Glitchworm, 44), (Ransomware, 11), (TrojanFile, 8)),
    ((PingFlooder, 54), (Glitchworm, 44), (Ransomware, 11), (TrojanFile, 8)),
    ((PingFlooder, 58), (Glitchworm, 46), (Ransomware, 13), (TrojanFile, 9)),
    ((PingFlooder, 62), (Glitchworm, 48), (Ransomware, 13), (TrojanFile, 9)),
    ((PingFlooder, 66), (Glitchworm, 50), (Ransomware, 14), (TrojanFile, 10)),
    (
        (KernelPanic, 1), (PingFlooder, 72), (Glitchworm, 54),
        (Ransomware, 16), (TrojanFile, 12),
    ),
)


def get_wave_spawns(wave_number: int) -> list[tuple[type[Enemy], int]]:
    """
    Mix preset enemies and raise levels every three waves, up to eight.
    """
    if not 1 <= wave_number <= len(WAVE_COMPOSITIONS):
        raise ValueError(
            f"wave_number must be between 1 and {len(WAVE_COMPOSITIONS)}"
        )

    enemy_level = min(
        ((wave_number - 1) // WAVES_PER_ENEMY_LEVEL) + 1,
        MAX_ENEMY_LEVEL,
    )

    composition = WAVE_COMPOSITIONS[wave_number - 1]

    spawned_counts = [0] * len(composition)
    spawns = []

    enemy_index = 0
    enemy_count = sum(count for _, count in composition)

    while enemy_index < enemy_count:
        for type_index in range(len(composition)):
            enemy_type, count = composition[type_index]

            if spawned_counts[type_index] < count:

                enemy_spawning = min(
                    count - spawned_counts[type_index],
                    MAX_ENEMY_SPAWNING
                )

                level = min(enemy_level, len(enemy_type.LEVELS))

                for _ in range(enemy_spawning):
                    spawned_counts[type_index] += 1
                    spawns.append((enemy_type, level))
                    enemy_index += 1

    return spawns
