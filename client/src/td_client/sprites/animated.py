from typing import List, Optional

import pygame

from .animation import AnimatedObject
from .base import YSortableSprite


class AnimatedSprite(YSortableSprite, AnimatedObject):
    """Animated sprite with frame-based animation.
    
    Supports frame-based animation with configurable speed
    Animations loop continuously
    Should be used for:
    - Units with walking/idle animations
    - Towers with attack/construction animations
    - Effects (explosions, particles, etc.)
    """
    
    def __init__(
        self, 
        x: float, 
        y: float, 
        frames: List[pygame.Surface],
        frame_duration: float = 0.1,
        fps: Optional[float] = None,
        entity_id: int = -1
    ):
        """Initialize animated sprite.
        
        Args:
            x: X position (used as midbottom.x)
            y: Y position (used as midbottom.y)
            frames: List of pygame.Surface frames for animation
            frame_duration: Duration of each frame in seconds (overridden by fps if provided)
            fps: Optional frames per second (alternative to frame_duration)
            entity_id: Unique identifier for linking to simulation entity
            
        Raises:
            ValueError: If frames list is empty
        """
        if not frames:
            raise ValueError("At least one frame is required")
        
        super().__init__(x, y, frames[0], entity_id)
        self.frames = frames
        self.current_frame_index = 0
        self.animation_time = 0.0
        
        if fps is not None:
            self.frame_duration = 1.0 / fps
        else:
            self.frame_duration = frame_duration
    
    def update_animation(self, dt: float) -> None:
        """Update animation state (implements AnimatedObject protocol).
        
        Args:
            dt: Delta time in seconds since last frame
        """
        if len(self.frames) <= 1:
            return
        
        self.animation_time += dt
        
        if self.animation_time >= self.frame_duration:
            self.animation_time = 0.0
            self.current_frame_index += 1
            
            if self.current_frame_index >= len(self.frames):
                    self.current_frame_index = 0
            
            self.image = self.frames[self.current_frame_index]
            self.rect = self.image.get_rect(midbottom=self.rect.midbottom)
    
    def update(self, dt: float):
        """Update sprite (legacy method, calls update_animation).
        
        Args:
            dt: Delta time in seconds since last frame
        """
        self.update_animation(dt)

