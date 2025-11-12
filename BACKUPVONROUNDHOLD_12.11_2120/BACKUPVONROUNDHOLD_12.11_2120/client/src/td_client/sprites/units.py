"""Unit sprites - movable entities."""
from typing import List

import pygame

from .animated import AnimatedSprite


class UnitSprite(AnimatedSprite):
    """Movable unit sprite (soldiers, etc.).
    
    Units can move around the map and are updated each frame.
    Position is set via rect.midbottom for correct ground reference.
    Inherits animation capabilities from AnimatedSprite.
    """
    
    def __init__(self, x: float, y: float, frames: List[pygame.Surface], speed: float = 40.0, entity_id: int = -1, **kwargs):
        """Init unit sprite
        
        Args:
            x: X position (used as midbottom.x)
            y: Y position (used as midbottom.y)
            frames: List of pygame.Surface frames for animation
            speed: Movement speed in pixels per second
            entity_id: Unique identifier for linking to simulation entity
            **kwargs: Additional arguments passed to AnimatedSprite (frame_duration, fps)
        """
        super().__init__(x, y, frames, entity_id=entity_id, **kwargs)
        self.speed = speed
    
    def update(self, dt: float):
        """Update unit animation only (position is driven by simulation)
        
        Args:
            dt: Delta time in seconds since last frame
        """
        # Only update animation, position is set by RenderManager from simulation state
        super().update(dt)
