from typing import Callable

import pygame

class Button:
    def __init__(
        self,
        position: tuple[int, int],
        unlit_img: pygame.Surface,
        lit_img: pygame.Surface,
        action: Callable[[], None], 
        anchor: str = "topleft"
    ):
        self.anchor = anchor
        self.position = position
        self.hovering = False
        self.action = action

        self.unlit_img = unlit_img
        self.lit_img = lit_img
        self.rect = self.unlit_img.get_rect(**{self.anchor: self.position})

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovering = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.action()

    def draw(self, window):
        image = self.lit_img if self.hovering else self.unlit_img
        window.blit(image, self.rect)

    def set_action(self, action: Callable[[], None]):
        self.action = action