from abc import ABC, abstractmethod

"""
App ──current_screen──> MainMenu    App controls the screen
App <──────app────────  Screen      Screen requests action from app
"""


class Screen(ABC):
    def __init__(self, app):
        '''
        Store the application that owns this screen.
        '''
        self.app = app

    @abstractmethod
    def handle_event(self, event):
        '''
        Handle an input event for the screen.
        '''
        pass

    @abstractmethod
    def update(self, dt):
        '''
        Update the screen state using the elapsed time since the last frame.
        '''
        pass

    @abstractmethod
    def draw(self, window):
        '''
        Draw the screen to the game window.
        '''
        pass
