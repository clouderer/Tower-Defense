"""Play tower and wave result sounds with a shared effects volume."""

from pathlib import Path
from typing import ClassVar

import pygame


class GameAudio:
    """Keep game sound effects and music ready to play."""

    ASSET_DIR: ClassVar[Path] = (
        Path(__file__).resolve().parents[1] / "asset_files" / "sfx"
    )

    SOUND_FILES: ClassVar[dict[str, tuple[str, float]]] = {
        "BIT_BLASTER": ("towers/bitblaster_pew.wav", 0.32),
        "FIREWALL_PULSE": ("towers/firewall_pew.wav", 0.4),
        "PROXY_BEAM": ("towers/proxybeam_laser.wav", 0.38),
        "CLOCK_THROTTLER": ("towers/clock_hum.wav", 0.22),
        "WAVE_CLEARED": ("gameplay/wave_cleared.wav", 0.45),
        "GAME_OVER": ("gameplay/game_over.wav", 0.5),
    }

    CHANNEL_COUNT: ClassVar[int] = 32

    def __init__(self, volume: float) -> None:
        """Load effects and reserve channels for the hum and results."""
        self.sounds = {}

        # Reserve channels for continuous clock humming and wave
        # result sfx.
        # NOTE clock towers share a single channel, therefore one sound.
        self.clock_channel = None
        self.result_channel = None

        # Initialize pygame audio system
        if pygame.mixer.get_init():
            pygame.mixer.set_num_channels(
                max(self.CHANNEL_COUNT, pygame.mixer.get_num_channels())
            )

            pygame.mixer.set_reserved(2)
            self.clock_channel = pygame.mixer.Channel(0)
            self.result_channel = pygame.mixer.Channel(1)

            # Load sounds into a dictionary
            self.sounds = {
                name: pygame.mixer.Sound(str(self.ASSET_DIR / filename))
                for name, (filename, _) in self.SOUND_FILES.items()
            }

        self.set_volume(volume)

    def set_volume(self, volume: float) -> None:
        """Change the volume of all sound effects."""
        self.volume = max(0.0, min(1.0, volume))
        for name, sound in self.sounds.items():
            # NOTE this is a pygame set_volume function
            sound.set_volume(self.volume * self.SOUND_FILES[name][1])

    def play_shot(self, tower_name: str) -> None:
        """Play one shot; the clock uses its continuous hum instead."""
        if tower_name != "CLOCK_THROTTLER":
            sound = self.sounds.get(tower_name)
            if sound is not None:
                sound.play()

    def set_clock_active(self, active: bool) -> None:
        """Hum while any clock has an enemy in range."""
        if self.clock_channel is None:
            return
        if active:
            if not self.clock_channel.get_busy():
                # Loop indefinitely and start with a FadeIn of 70ms
                self.clock_channel.play(
                    self.sounds["CLOCK_THROTTLER"], loops=-1, fade_ms=70
                )
        else:
            self.clock_channel.stop()

    def play_event(self, event_name: str) -> None:
        """Play a wave result even when shooting channels are busy."""
        sound = self.sounds.get(event_name)
        if sound is not None and self.result_channel is not None:
            self.result_channel.play(sound)

    def stop(self) -> None:
        """Stop all effects when gameplay is interrupted."""
        for sound in self.sounds.values():
            sound.stop()
