from pathlib import Path

import pygame

from ..screen import Screen
from ...ui.button import Button


class Tutorial(Screen):
    TUTORIAL_ASSET_DIR = Path(__file__).resolve(
    ).parents[3] / "asset_files" / "tutorial"

    PLAY_UNLIT_IMG = pygame.image.load(TUTORIAL_ASSET_DIR / "back_unlit.png")
    PLAY_LIT_IMG = pygame.image.load(TUTORIAL_ASSET_DIR / "back_lit.png")

    def __init__(self, app):
        '''
        Initialize the tutorial step counter and back button.
        '''
        super().__init__(app)

        self.step: int = 1

        self.back_button = Button(
            position=(12, 12),
            unlit_img=self.PLAY_UNLIT_IMG,
            lit_img=self.PLAY_LIT_IMG,
            action=self.app.get_map_selection,
        )

    def handle_event(self, event):
        '''
        Advance the tutorial on a left click and handle the back button.
        '''
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self.step += 1

        self.back_button.handle_event(event)

    def update(self, dt):
        '''
        Update the tutorial; no animated state is implemented yet.
        '''
        pass

    def draw(self, window):
        '''
        Draw the tutorial; its page content is not implemented yet.
        '''
        pass
