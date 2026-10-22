import pygame


class Sprite(pygame.sprite.Sprite):
    """Animate frames loaded from a sprite sheet."""

    # Note the x_cnt, y_cnt, fps are set for the screen animations
    def __init__(self, image, x_cnt=8, y_cnt=10, position=(0, 0), fps=18):
        """
        Load the sheet and place the first frame at the given position.
        """
        super().__init__()
        self.frames = self.get_frames(image, x_cnt, y_cnt)
        self.frame_index = 0
        self.time = 0
        self.fps = fps

        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=position)

    def update(self, dt):
        """
        Advance the animation by the time passed since the last update.
        """
        self.time += dt

        frame_duration = 1 / self.fps
        frames_elapsed = int(self.time / frame_duration)
        if frames_elapsed:
            self.time -= frames_elapsed * frame_duration
            self.frame_index = (
                self.frame_index + frames_elapsed
            ) % len(self.frames)
            self.image = self.frames[self.frame_index]

    # @generated "partially" GitHub Copilot: 
    # Recommended subsurface function.
    @staticmethod
    def get_frames(image, x_cnt, y_cnt):
        """Split a sprite sheet into frames by its columns and rows."""
        sheet = pygame.image.load(image).convert_alpha()
        sheet_width, sheet_height = sheet.get_size()

        frame_width = sheet_width // x_cnt
        frame_height = sheet_height // y_cnt

        frames = [
            sheet.subsurface(pygame.Rect(
                i * frame_width,
                j * frame_height,
                frame_width,
                frame_height,
            ))
            for j in range(y_cnt)
            for i in range(x_cnt)
        ]

        return frames
