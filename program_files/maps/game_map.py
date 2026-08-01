"""
Good idea would be to have maps with different sizes
for our purposes all maps will have the same diemsnions: 

    350x600  <--- This size was selected as optimal by me 
    
    It is large enough for the game, and small enough to have it as a little side window
"""

class GameMap: 
    def __init__(self, image, enemy_path):
        self.image =  image
        self.enemy_path = enemy_path
        self.width, self.height = image.get_size() 
