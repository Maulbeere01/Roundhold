import pygame


class BaseSprite(pygame.sprite.Sprite):
    """Base sprite class with common functionality
    
    All game sprites should inherit from this class. Provides standard
    position management and update stubs
    """
    
    def __init__(self, x: float, y: float, image: pygame.Surface, entity_id: int = -1):
        """Init base sprite
        
        Args:
            x: X position (used as midbottom.x for proper ground reference)
            y: Y position (used as midbottom.y for proper ground reference)
            image: pygame.Surface for the sprite
            entity_id: Unique identifier for linking to simulation entity
        """
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.entity_id = entity_id
    
    def set_position(self, x: float, y: float) -> None:
        """Update sprite position.
        
        Args:
            x: New X position (midbottom.x)
            y: New Y position (midbottom.y)
        """
        self.rect.midbottom = (x, y)
    
    def update(self, *args, **kwargs):
        """Update sprite state.
        
        Override in subclasses for custom behavior
        """
        pass


class YSortableSprite(BaseSprite):
    """Sprite that supports Y-sorting for depth rendering
    
    Uses rect.bottom for sorting, creating the illusion of depth
    where sprites with higher bottom values appear in front
    """
    
    def __init__(self, x: float, y: float, image: pygame.Surface, entity_id: int = -1):
        """Initialize Y-sortable sprite
        
        Args:
            x: X position (used as midbottom.x)
            y: Y position (used as midbottom.y)
            image: pygame.Surface for the sprite
            entity_id: Unique identifier for linking to simulation entity
        """
        super().__init__(x, y, image, entity_id)
    
    def get_sort_key(self) -> float:
        """Get sort key for Y-sorting
        
        Lower values render first (behind), higher values render last (in front)
        
        Returns:
            Sort key value (rect.bottom)
        """
        return self.rect.bottom
