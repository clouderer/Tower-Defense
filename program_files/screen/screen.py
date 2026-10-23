"""Define the methods shared by all game screens."""

from __future__ import annotations
from abc import ABC, abstractmethod


class Screen(ABC):
    """
    Store the app and define how a screen handles input and drawing.
    """

    def __init__(self, app: App) -> None:
        """Store the app that controls this screen."""
        self.app = app

    def on_suspend(self) -> None:
        """
        Handle another screen opening above this screen.

        Note: In this current state only Gameplay uses on_suspend
        function.
        """
        pass

    def on_resume(self) -> None:
        """
        Handle returning to this screen after closing another screen.

        Note: In this current state only Gameplay uses on_suspend
        function.
        """
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event) -> None:
        """Handle an input event for the screen."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the screen using the time since the last frame."""
        pass

    @abstractmethod
    def draw(self, window: pygame.display) -> None:
        """Draw the screen in the game window."""
        pass
