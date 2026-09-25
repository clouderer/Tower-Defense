from pathlib import Path

import pygame

from ..screen import Screen


class MapSelection(Screen):

    def __init__(self, app):
        super().__init__(app)

    def handle_event(self, event):
        if event == pygame.MOUSEBUTTONDOWN: 
            if event.button == 1: 
                # [TO DO] Create Buttons etc. 

    def update(self, dt):
        pass

    def draw(self, window):
        pass