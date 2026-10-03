from dataclasses import dataclass, field

import pygame

from .screen.types.gameplay.gameplay import Gameplay
from .screen.types.main_menu import MainMenu
from .screen.types.map_selection import MapSelection
from .screen.types.settings_menu import SettingsMenu

# [TO DO] Settings will be able to access the Volume, the volume has to be shared by all the screens, therefore needs to be stored in the App class. The volume will be passed to the SettingsMenu and Gameplay screens, which will use it to set the volume of the music and sound effects.
@dataclass 
class Volume: 
    music_volume: float = 1.0
    sfx_volume: float = 1.0

class App:
    DISPLAY_WIDTH = 600
    DISPLAY_HEIGHT = 350

    def __init__(self):
        pygame.init()

        self.window = pygame.display.set_mode((self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.volume = Volume()

        self.screen_stack = [MainMenu(self)]

    #____SCREEN_TRANSITION_METHODS____
    @property
    def current_screen(self):
        '''
        Returns the current screen, which is the screen at the top of the screen stack.
        '''
        return self.screen_stack[-1]

    def change_screen(self, screen):
        '''
        Removes all screens from the screen stack and sets the current screen to the given screen.
        Used for permanent transitions. 
        '''
        self.screen_stack[:] = [screen]

    def push_screen(self, screen):
        '''
        Adds a new screen to the top of the screen stack.
        '''
        self.screen_stack.append(screen)

    def pop_screen(self):
        '''
        Removes the current screen from the screen stack.
        '''
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()


    # ____SCREEN_FETCHING_METHODS____
    def get_main_menu(self):
        '''
        Changes the current screen to the main menu.
        '''
        self.change_screen(MainMenu(self))

    def get_map_selection(self):
        '''
        Changes the current screen to the map selection menu.
        '''
        self.change_screen(MapSelection(self))

    def get_gameplay(self, game_map):
        '''
        Changes the current screen to the gameplay screen.
        '''
        self.change_screen(Gameplay(self, game_map=game_map))

    def get_settings(self):
        '''
        Adds the settings menu to the screen stack.
        '''
        self.push_screen(SettingsMenu(self))

    #____RUN_METHOD____
    def run(self):
        '''
        Runs the main game loop, which handles events, updates the current screen, and draws the current screen.
        '''
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
