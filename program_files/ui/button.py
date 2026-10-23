"""Create an interactable button and handle the buttons actions."""

from __future__ import annotations
from typing import Callable

import pygame


# @generated "partially" GitHub Copilot: Callable action and set_action.
class Button:
    """Display a button and call its action when clicked."""

    def __init__(
        self,
        position: tuple[int,int],
        unlit_img: pygame.image,
        lit_img: pygame.image,

        # Callable symbolizes a callable type
        # In the case of a button the Callable takes no arguments
        # and returns None
        action: Callable[[], None],
        anchor: str = "topleft",
    ) -> None:
        """Store the button images, position, and action."""
        self.anchor = anchor
        self.position = position
        self.hovering = False
        self.action = action

        self.unlit_img = unlit_img
        self.lit_img = lit_img

        # Note the use of dictionary unpacking
        # The anchor and position attributes are packed into a
        # dictionary.
        # Using the ** they are unpacked into keyword arguments and
        # used in the function
        # https://www.sitepoint.com/python/dictionaries-unpacking/
        self.rect = self.unlit_img.get_rect(**{self.anchor: self.position})

    def handle_event(self, event: pygame.event) -> bool:
        """
        Update hover state and return whether the instance was clicked.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovering = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()
                return True

        return False

    def draw(self, window: pygame.display) -> None:
        """Draw the lit image when the mouse is over the button."""
        image = self.lit_img if self.hovering else self.unlit_img
        window.blit(image, self.rect)

    def set_action(self, action: Callable[[], None]) -> None:
        """Set the action to call when the button is clicked."""
        self.action = action
