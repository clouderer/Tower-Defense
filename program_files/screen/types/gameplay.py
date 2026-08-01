from screen.screen import Screen

class Gameplay(Screen): 
    def __init__ (self, app, selected_map): 
            super().__init__(app)
            self.game_map = selected_map

    def handle_event(self, event):
        return super().handle_event(event)

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
        window.fill("lightblue")