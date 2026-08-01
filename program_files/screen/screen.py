from abc import ABC, abstractmethod

"""
App ──current_screen──> MainMenu    App controls the screen
App <──────app────────  Screen      Screen requests action from app
"""

class Screen(ABC): 
    def __init__(self, app): 
        self.app = app 

    @abstractmethod
    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    @abstractmethod
    def draw(self, window):
        pass