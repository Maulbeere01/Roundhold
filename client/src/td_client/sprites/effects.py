import pygame
from .animated import AnimatedSprite

class OneShotEffect(AnimatedSprite):
    """A sprite that plays an animation once and then kills itself."""
    
    def __init__(self, x: float, y: float, frames: list[pygame.Surface], fps: float = 15.0):
        super().__init__(x, y, frames, fps=fps)
        # Set the initial position centered on x, y
        self.rect = self.image.get_rect(center=(x, y))
        self.current_frame_index = 0
        self.loop = False 
        
    def update_animation(self, dt: float) -> None:
        """Update animation and kill sprite when finished."""
        self.animation_time += dt
        
        if self.animation_time >= self.frame_duration:
            self.animation_time = 0.0
            self.current_frame_index += 1
            
            # If we reached the end of the frames, destroy the sprite
            if self.current_frame_index >= len(self.frames):
                self.kill() 
                return

            # Save the current center position
            old_center = self.rect.center
            
            # Update the image
            self.image = self.frames[self.current_frame_index]
            
            # Re-center the rect based on the new image size
            self.rect = self.image.get_rect(center=old_center)