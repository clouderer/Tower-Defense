from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Union

import pygame


ColorValue = Union[
    str, pygame.Color, tuple[int, int, int],
    tuple[int, int, int, int]
]

PIXEL_FONT = str(
    Path(__file__).resolve().parents[2]
    / "asset_files"
    / "fonts"
    / "Silkscreen-Regular.ttf"
)

# maxsize is set to one because only one font type is being loaded
# @generated "fully" GitHub Copilot: Font loading function
@lru_cache(maxsize=1)
def get_font(font_path: Optional[str], font_size: int) -> pygame.font.Font:
    """Reuse loaded fonts with the same file path and size."""
    return pygame.font.Font(font_path, font_size)


@dataclass
class TextObject:
    """Store the text, font, color, and position of a text label."""

    font: Optional[str] = PIXEL_FONT
    font_size: int = 13
    text: str = ""
    antialias: bool = True
    color: ColorValue = "White"
    background: Optional[ColorValue] = None
    anchor: str = "center"
    position: tuple[int, int] = (0, 0)

    def draw(self, window: pygame.Surface):
        """Draw the text at its position using the selected anchor."""
        font = get_font(self.font, self.font_size)
        surface = font.render(
            self.text, self.antialias, self.color, self.background
        )
        rect = surface.get_rect(**{self.anchor: self.position})
        window.blit(surface, rect)
