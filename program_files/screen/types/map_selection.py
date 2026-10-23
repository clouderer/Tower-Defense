"""Screen displaying the map options."""

from __future__ import annotations
from pathlib import Path
from typing import ClassVar

import pygame

from ..screen import Screen
from ...maps.game_map import GameMap, NEON_GRID_MAP
from ...ui.button import Button
from ...ui.sprite import Sprite


class MapOption:
    """Store the image and game map for one map option."""

    def __init__(
        self,
        image_path: Path,
        position: tuple[int,int],
        gamemap: GameMap,
    ) -> None:
        """Load the map image and store its position and game map."""
        self.image = pygame.image.load(image_path)
        self.position = position
        self.hovering = False
        self.rect = self.image.get_rect(topleft=position)
        self.gamemap = gamemap


class MapSelection(Screen):
    """Display the available maps and open the selected map."""

    MAP_OPT_ASSET_DIR: ClassVar[Path] = Path(__file__).resolve(
    ).parents[3] / "asset_files" / "map_selection"
    MAP_ASSET_DIR: ClassVar[Path] = Path(__file__).resolve(
    ).parents[3] / "asset_files" / "maps"

    SELECT_MENU_IMG: ClassVar[pygame.image] = pygame.image.load(
        MAP_OPT_ASSET_DIR / "map_selection0.png")
    FRAME_UNLIT_IMG: ClassVar[pygame.image] =  pygame.image.load(
        MAP_OPT_ASSET_DIR / "frame_unlit.png")
    FRAME_LIT_IMG: ClassVar[pygame.image] = pygame.image.load(
        MAP_OPT_ASSET_DIR / "frame_lit.png")

    BACK_BUTTON_LIT_IMG: ClassVar[pygame.image] = pygame.image.load(
        MAP_OPT_ASSET_DIR / "back_lit.png")
    BACK_BUTTON_UNLIT_IMG: ClassVar[pygame.image] = pygame.image.load(
        MAP_OPT_ASSET_DIR / "back_unlit.png")

    # These offsets are used for offsetting the map 
    # into the frame positions.
    # The width of the frame is exactly one pixel in x,y directions.
    X_OFFSET: ClassVar[int] = 1
    Y_OFFSET: ClassVar[int] = 1

    # The menu has space for three maps. Only the first map is
    # available for the time being.
    MAP_PLACEMENTS: ClassVar[list[tuple[int,int]]] = [
        (37, 101),
        (217, 101),
        (397, 101)]

    MAP_IMAGES: ClassVar[list[str]] = [
        "map_option1.png",
        "map_option2.png",
        "map_option3.png"
    ]

    def __init__(self, app: App) -> None:
        """Create the map options, back button, and menu animation."""
        super().__init__(app)
        self.map_options = [
            MapOption(
                self.MAP_OPT_ASSET_DIR / self.MAP_IMAGES[0],
                self.MAP_PLACEMENTS[0],
                NEON_GRID_MAP,
            ),
            # Additional maps have not been added yet.
        ]

        self.back_button = Button(
            position=(12, 12),
            unlit_img=self.BACK_BUTTON_UNLIT_IMG,
            lit_img=self.BACK_BUTTON_LIT_IMG,
            action=app.get_main_menu
        )

        self.overlay_sprite = Sprite(
            self.MAP_OPT_ASSET_DIR / "map_selection_overlay_sheet.png"
        )
        self.sprites = pygame.sprite.Group(self.overlay_sprite)

    def handle_event(self, event: pygame.event) -> None:
        """
        Highlight map options and handle map and back button clicks.
        """
        if event.type == pygame.MOUSEMOTION:
            for map_opt in self.map_options:
                map_opt.hovering = map_opt.rect.collidepoint(event.pos)
        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            for map_opt in self.map_options:
                if map_opt.rect.collidepoint(event.pos):
                    self.app.get_gameplay(map_opt.gamemap)

        self.back_button.handle_event(event)

    def update(self, dt: float) -> None:
        """Update the map selection animation."""
        self.overlay_sprite.update(dt)

    def draw(self, window: pygame.display) -> None:
        """Draw the background, map options, frames, and back button."""
        window.blit(self.SELECT_MENU_IMG, (0, 0))
        self.sprites.draw(window)

        for map_opt in self.map_options:
            window.blit(map_opt.image, map_opt.position)

            x, y = map_opt.position
            frame_position = (x - self.X_OFFSET, y - self.Y_OFFSET)

            if map_opt.hovering:
                window.blit(self.FRAME_LIT_IMG, frame_position)
            else:
                window.blit(self.FRAME_UNLIT_IMG, frame_position)

        self.back_button.draw(window)
