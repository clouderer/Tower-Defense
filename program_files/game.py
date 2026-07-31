import pygame

class Game: 
    def __init__(self): 
        pygame.init()

        # [TO DO] - FILL OUT THE WIDTH AND HEIGHT ACCORDINGLY TO THE SELECTED MAP 

        self.width  = 250 
        self.height = 250

        self.win = pygame.display.set_mode((self.width, self.height))


    #____METHODS____ 

    def run(self):
        running = True 

        while running: 
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    running = False

            pygame.display.update()

        pygame.quit() 