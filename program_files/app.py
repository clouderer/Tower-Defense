import pygame

from screen.types.main_menu     import MainMenu
from screen.types.map_selection import MapSelection
from screen.types.gameplay      import Gameplay
from screen.types.settings_menu import SettingsMenu
from screen.types.pause_menu    import PauseMenu
from screen.types.result_screen import ResultScreen


from maps.game_map              import GameMap
DISPLAY_WIDTH = 600 
DISPLAY_HEIGHT = 350

class App: 
    def __init__(self): 
        pygame.init()

        self.window = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.current_screen = Gameplay(self) # [TO DO]

    #____METHODS____ 

    def change_screen(self, new_screen): 
        self.current_screen = new_screen

    def run(self):
        while self.running: 
            dt = self.clock.tick(60) / 1000

            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    self.running = False

                self.current_screen.handle_event(event)

            self.current_screen.update(dt)
            self.current_screen.draw(self.window)

            pygame.display.update() 

        pygame.quit() 

tmp_game_map = GameMap()

game = App()
game.run()
