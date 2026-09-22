from dataclasses import dataclass
from typing import Optional, Union

import pygame


ColorValue = Union[str, pygame.Color, tuple[int, int, int], tuple[int, int, int, int]]

#[TO DO] Try and get a different font

@dataclass
class TextObject:
    font: Optional[str] = "freesansbold.ttf"
    font_size: int = 13
    text: str = ""
    antialias: bool = True
    color: ColorValue = "White"
    background: Optional[ColorValue] = None
    anchor: str = "center"
    position: tuple[int, int] = (0, 0)

    def draw(self, window: pygame.Surface):
        font = pygame.font.Font(self.font, self.font_size)
        surface = font.render(
            self.text, self.antialias, self.color, self.background
        )
        rect = surface.get_rect(**{self.anchor: self.position})
        window.blit(surface, rect)
