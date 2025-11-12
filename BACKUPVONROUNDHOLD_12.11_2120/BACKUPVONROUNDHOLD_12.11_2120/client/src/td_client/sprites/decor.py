"""Decoration sprites - static decorative elements."""
import pygame

from .base import YSortableSprite


class DecorSprite(YSortableSprite):
    """Static decorative sprite (rocks, plants, etc.).
    
    Decor sprites are purely visual and do not have game logic.
    """
    
    def __init__(self, x: float, y: float, image: pygame.Surface, entity_id: int = -1):
        """Initialize decor sprite.
        
        Args:
            x: X position (used as midbottom.x)
            y: Y position (used as midbottom.y)
            image: pygame.Surface for the decoration
            entity_id: Unique identifier for linking to simulation entity
        """
        super().__init__(x, y, image, entity_id)
