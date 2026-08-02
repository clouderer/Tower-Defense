import pygame

from ..screen import Screen

class Gameplay(Screen): 
    def __init__ (self, app, selected_map): 
            super().__init__(app)
            self.game_map = selected_map

    def handle_event(self, event):
        pass

        """
        [TO DO]: 
        EXPECTABLE BEHAVIOR 
            Tower actions
                Place Tower 
                Upgrade Tower 
                Remove Tower 
            View Enemy Health 
            Skip Wave 
            Pause 
                Reach Settings 
            Quit 
        """

    def draw(self, window):
        window.blit(self.game_map.image, (0,0))

        
        for position in self.game_map.tower_positions: 
            x, y = position

            pygame.draw.rect(
                window,
                "gray", 
                (x,y, 24, 24) ) 
        

        pygame.draw.lines(
             window, "red", False, self.game_map.enemy_path, 1
        )

        for position in self.game_map.enemy_path: 
             x,y = position

             pygame.draw.circle(
                  window, "green", (x,y), 1.0
             )