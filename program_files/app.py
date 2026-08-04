import pygame

from .screen.types.gameplay.gameplay    import Gameplay
from .maps.game_map                     import GameMap
from pathlib                            import Path

DISPLAY_WIDTH = 600 
DISPLAY_HEIGHT = 350


tmp_path = [
    (1,176),
    (26,176),
    (26,76),
    (126,76),
    (126,176),
    (76,176),
    (76,276),
    (226,276),
    (226,176),
    (176,176),
    (176,76),
    (326,76),
    (326, 176),
    (276, 176),
    (276, 276),
    (426, 276),
    (426, 176),
    (376, 176),
    (376, 76),
    (526, 76),
    (526, 201)
]

tmp_tower_positions = [
    (51,101), (76,101),
    (51,126), (76,126),

    (126,26),
    (151,26),

    (151,301),
    (176,301),

    (101,201),
    (126,201),
    (151,201),
    (176,201),

    (101,226),
    (126,226),
    (151,226),
    (176,226),

    (201,101),
    (226,101),
    (251,101),
    (276,101),

    (201,126),
    (226,126),
    (251,126),
    (276,126),

    (301,26),
    (326,26),
    (351,26),
    (376,26),
    (401,26),

    (301,201),
    (326,201),
    (351,201),
    (376,201),

    (301,226),
    (326,226),
    (351,226),
    (376,226),

    (401,101),
    (426,101),
    (451,101),
    (476,101),

    (401,126),
    (426,126),
    (451,126),
    (476,126),

    (451, 201),
    (451, 226),
    (451, 251),

    (376,301),
    (401,301),
]

tmp_image_path = Path(__file__).resolve().parents[1]/"asset_files"/"maps"/"neon_grid.png"
tmp_image = pygame.image.load(tmp_image_path)
tmp_game_map = GameMap(tmp_image, tmp_path, tmp_tower_positions)

class App: 
    def __init__(self): 
        pygame.init()

        self.window = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.current_screen = Gameplay(self, tmp_game_map) # [TO DO]

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

            self.current_screen.draw(self.window)
            self.current_screen.update(dt)

            pygame.display.update() 

        pygame.quit() 

game = App()
game.run()
