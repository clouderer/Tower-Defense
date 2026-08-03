import pygame

from ..screen import Screen
from ...enemy.enemy import Enemy

class Gameplay(Screen): 
    def __init__ (self, app, selected_map): 
            super().__init__(app)
            self.game_map = selected_map

            self.enemy = Enemy(self.game_map.enemy_path)

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

        if self.enemy.reached_end: 
            font = pygame.font.Font("freesansbold.ttf", 32)
            text = font.render("GAME OVER", True, "White")
            text_rect = text.get_rect()
            text_rect.center = (300,175)
            window.blit(text, text_rect)
            return 
        
        self.enemy.draw(window)

    def update(self, dt):
        self.enemy.update(dt)