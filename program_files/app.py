"""Create the game window and manage the active screen."""

from __future__ import annotations
from dataclasses import dataclass
from ctypes import WinDLL, WinError, get_last_error, wintypes
from typing import ClassVar

import pygame

from .screen.types.gameplay.gameplay import Gameplay
from .screen.types.main_menu import MainMenu
from .screen.types.map_selection import MapSelection
from .screen.types.settings_menu import SettingsMenu


@dataclass
class Volume:
    """Store the volume settings shared by the game screens."""

    music_volume: float = 1.0
    sfx_volume: float = 1.0


class App:
    """Manage the game window, screens, and main loop."""

    DISPLAY_WIDTH: ClassVar[int] = 600
    DISPLAY_HEIGHT: ClassVar[int] = 350
    WINDOW_X: ClassVar[int] = 100
    WINDOW_Y: ClassVar[int] = 100

    def __init__(self) -> None:
        """Set up Pygame, the game window, and the main menu."""
        pygame.init()

        self.window = pygame.display.set_mode(
            (self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))

        pygame.display.set_caption('CPU Overclock')

        self.clock = pygame.time.Clock()
        self.running = True

        self.volume = Volume()

        self.screen_stack = [MainMenu(self)]

    @property
    def current_screen(self) -> Screen:
        """Return the screen currently shown in the game window."""
        return self.screen_stack[-1]

    def change_screen(self, screen: Screen) -> None:
        """Replace the current screens with the selected screen."""
        self.screen_stack[:] = [screen]

    def push_screen(self, screen: Screen) -> None:
        """Open another screen and suspend the screen underneath it."""
        self.current_screen.on_suspend()
        self.screen_stack.append(screen)

    def pop_screen(self) -> None:
        """Close the current screen and resume the previous screen."""
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()
            self.current_screen.on_resume()

    def get_main_menu(self) -> None:
        """Open the main menu."""
        self.change_screen(MainMenu(self))

    def get_map_selection(self) -> None:
        """Open the map selection screen."""
        self.change_screen(MapSelection(self))

    def get_gameplay(self, game_map: GameMap) -> None:
        """Start a game on the selected map."""
        self.change_screen(Gameplay(self, game_map=game_map))

    def get_settings(self) -> None:
        """Open settings above the current screen."""
        self.push_screen(SettingsMenu(self))

    def run(self) -> None:
        """
        Handle input, update the active screen, and draw each frame.
        """
        while self.running:
            # Game clocks upper bound is 60fps
            # Delta time is recalculated from miliseconds to seconds
            # so it's easier to understand
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                self.current_screen.handle_event(event)

            if not self.running:
                break

            self.current_screen.update(dt)
            self.current_screen.draw(self.window)

            pygame.display.update()

        pygame.quit()


def main() -> None:
    """Create the application and start the game."""
    game = App()
    game.run()


if __name__ == "__main__":
    main()
