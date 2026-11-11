"""Draw and drag a slider for a volume between zero and one."""

from collections.abc import Callable
from typing import ClassVar

import pygame

from .text_object import TextObject


class VolumeSlider:
    """Show a volume label, percentage, and draggable slider."""

    TEXT_COLOR: ClassVar[str] = "#9feef8"
    TRACK_COLOR: ClassVar[str] = "#052444"
    FILL_COLOR: ClassVar[str] = "#075296"
    HANDLE_COLOR: ClassVar[str] = "#9feef8"

    def __init__(
        self,
        label: str,
        position: tuple[int, int],
        value: float,
        on_change: Callable[[float], None],
        width: int = 300,
    ) -> None:
        """Place the slider and store what to do when it changes."""
        self.track = pygame.Rect(*position, width, 8)
        self.value = max(0.0, min(1.0, value))
        self.on_change = on_change
        self.dragging = False
        self.label = TextObject(
            text=label,
            font_size=16,
            color=self.TEXT_COLOR,
            anchor="bottomleft",
            position=(self.track.left, position[1] - 12),
        )
        self.percentage = TextObject(
            font_size=14,
            color=self.TEXT_COLOR,
            anchor="bottomright",
            position=(self.track.right, position[1] - 12),
        )

    def set_from_mouse(self, x_position: int) -> None:
        """Keep the volume within the slider and apply it right away."""
        self.value = max(
            0.0, min(1.0, (x_position - self.track.left) / self.track.width)
        )
        self.on_change(self.value)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Allow clicking the track or dragging the handle."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # NOTE: Increase the collider for easier interaction
            if self.track.inflate(20, 24).collidepoint(event.pos):
                self.dragging = True
                self.set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_from_mouse(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.set_from_mouse(event.pos[0])
            self.dragging = False
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.dragging = False

    def draw(self, window: pygame.Surface) -> None:
        """Draw the current volume in the settings screen's colors."""
        self.label.draw(window)
        self.percentage.text = f"{round(self.value * 100)}%"
        self.percentage.draw(window)
        pygame.draw.rect(window, self.TRACK_COLOR, self.track)
        filled_width = round(self.track.width * self.value)
        if filled_width:
            fill = self.track.copy()
            fill.width = filled_width
            pygame.draw.rect(window, self.FILL_COLOR, fill)
        handle = pygame.Rect(0, 0, 12, 20)
        handle.center = (self.track.left + filled_width, self.track.centery)
        pygame.draw.rect(window, self.HANDLE_COLOR, handle)
        pygame.draw.rect(window, self.FILL_COLOR, handle, width=2)
