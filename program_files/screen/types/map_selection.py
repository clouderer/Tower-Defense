from pathlib import Path

import pygame

from ..screen import Screen
from ...maps.game_map import GameMap, NEON_GRID_MAP
from ...ui.button import Button

class MapOption:
    def __init__(self,image_path: Path, position: tuple, gamemap: GameMap): 
        self.image = pygame.image.load(image_path)
        self.position = position
        self.hovering = False
        self.rect = self.image.get_rect(topleft = position)
        self.gamemap = gamemap
        

class MapSelection(Screen):
    MAP_OPT_ASSET_DIR = Path(__file__).resolve().parents[3] / "asset_files" / "map_selection"
    MAP_ASSET_DIR = Path(__file__).resolve().parents[3] / "asset_files" / "maps"

    SELECT_MENU_IMG = pygame.image.load(MAP_OPT_ASSET_DIR / "map_selection0.png")
    FRAME_UNLIT_IMG = pygame.image.load(MAP_OPT_ASSET_DIR/"frame_unlit.png")
    FRAME_LIT_IMG = pygame.image.load(MAP_OPT_ASSET_DIR/"frame_lit.png")

    # [TO DO] Make the buttons
    BACK_BUTTON_LIT_IMG = pygame.image.load(MAP_OPT_ASSET_DIR/ "back_lit.png")
    BACK_BUTTON_UNLIT_IMG = pygame.image.load(MAP_OPT_ASSET_DIR/ "back_unlit.png")

    X_OFFSET = Y_OFFSET = 1

    # These additional unused attributes are here for future develeopment - for now we are only working with one map
    MAP_PLACEMENTS = [
        (37, 101),
        (217, 101),
        (397, 101)]

    MAP_IMAGES = [
        "map_option1.png",
        "map_option2.png",
        "map_option3.png"
    ]

    def __init__(self, app):
        super().__init__(app)
        self.map_options = [
            MapOption(
                self.MAP_OPT_ASSET_DIR/self.MAP_IMAGES[0],
                self.MAP_PLACEMENTS[0],
                NEON_GRID_MAP,
            ),
            # [TO DO]: Create and add maps       
        ]

        self.back_button = Button(
            position = (12, 12),
            unlit_img = self.BACK_BUTTON_UNLIT_IMG, 
            lit_img = self.BACK_BUTTON_LIT_IMG, 
            action = app.get_main_menu
        )

    def handle_event(self, event):
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

    def update(self, dt):
        pass

    def draw(self, window):
        window.blit(self.SELECT_MENU_IMG, (0, 0))
        
        for map_opt in self.map_options: 
            window.blit(map_opt.image, map_opt.position)

            x,y = map_opt.position 
            frame_position = (x - self.X_OFFSET, y - self.Y_OFFSET)

            if map_opt.hovering: 
                window.blit(self.FRAME_LIT_IMG, frame_position)
            else: 
                window. blit(self.FRAME_UNLIT_IMG, frame_position)

        self.back_button.draw(window)


