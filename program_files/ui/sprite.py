import pygame
from pathlib import Path

class Sprite(pygame.sprite.Sprite): 
    def __init__(self, image, x_cnt = 8, y_cnt = 10, position = (0,0), fps = 18): 
        super().__init__()
        self.frames = self.get_frames(image, x_cnt, y_cnt)
        self.frame_index = 0
        self.time = 0
        self.fps = fps

        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft = position)

    def update(self, dt): 
        self.time += dt
        if self.time >= 1 / self.fps:
            self.time -= 1 / self.fps
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

    @staticmethod
    def get_frames(image, x_cnt, y_cnt):
        sheet = pygame.image.load(image).convert_alpha()
        sheet_width, sheet_height = sheet.get_size()

        frame_width = sheet_width // x_cnt
        frame_height = sheet_height // y_cnt

        frames = [
            sheet.subsurface(pygame.Rect(i * frame_width, j * frame_height, frame_width, frame_height))
            for j in range(y_cnt)
            for i in range(x_cnt)
        ]

        return frames