from typing import Callable

import pygame

# @generated "partially" GitHub Copilot: Callable action and set_action.


class Button:
    '''
    Universal UI element for buttons.
    '''

    def __init__(
        self,
        position: tuple[int, int],
        unlit_img: pygame.Surface,
        lit_img: pygame.Surface,
        action: Callable[[], None],
        anchor: str = "topleft"
    ):
        '''
        Initialize a button's images, position, hover state, and callback.
        '''
        self.anchor = anchor
        self.position = position
        self.hovering = False
        self.action = action

        self.unlit_img = unlit_img
        self.lit_img = lit_img
        self.rect = self.unlit_img.get_rect(**{self.anchor: self.position})

    def handle_event(self, event):
        '''
        Update hover state or invoke the callback when the button is clicked.
        '''
        if event.type == pygame.MOUSEMOTION:
            self.hovering = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

    def draw(self, window):
        '''
        Draw the lit or unlit button image according to its hover state.
        '''
        image = self.lit_img if self.hovering else self.unlit_img
        window.blit(image, self.rect)

    def set_action(self, action: Callable[[], None]):
        '''
        Set the function to call when the button is clicked.
        '''
        self.action = action
