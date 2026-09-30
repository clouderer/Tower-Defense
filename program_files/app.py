from dataclasses import dataclass, field

import pygame

from .screen.types.gameplay.gameplay import Gameplay
from .screen.types.main_menu import MainMenu
from .screen.types.map_selection import MapSelection
from .screen.types.settings_menu import SettingsMenu

# [TO DO] Replace it with a setting which will be held by the App 
@dataclass
class Volume: 
    music_volume: float = 0.5
    sfx_volume: float = 0.5

class App:
    DISPLAY_WIDTH = 600
    DISPLAY_HEIGHT = 350

    def __init__(self):
        pygame.init()

        self.window = pygame.display.set_mode((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.volume = Volume()

        self.current_screen = MainMenu(self)

    # ____METHODS____

    def change_screen(self, new_screen):
        self.current_screen = new_screen

    def get_main_menu(self):
        self.change_screen(MainMenu(self))

    def get_map_selection(self):
        self.change_screen(MapSelection(self))

    def get_gameplay(self, game_map):
        self.change_screen(Gameplay(self, game_map=game_map))

    def get_settings(self):
        self.change_screen(SettingsMenu(self))

    def get_pause_menu(self):
        # self.change_screen(PauseMenu(self))
        pass

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                self.current_screen.handle_event(event)

            self.current_screen.draw(self.window)
            self.current_screen.update(dt)

            pygame.display.update()

        pygame.quit()

game = App()
game.run()
