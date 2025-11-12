from typing import Optional, Tuple

import pygame

from .base import YSortableSprite


class BuildingSprite(YSortableSprite):
    """Static building sprite (castles, towers, etc.).
    
    Buildings are static structures that do not move or animate.
    Position is set via rect.midbottom for correct ground reference.
    """
    
    def __init__(
        self,
        x: float,
        y: float,
        image: pygame.Surface,
        entity_id: int = -1,
        range_px: Optional[float] = None,
        range_fill_color: Tuple[int, int, int, int] = (0, 180, 255, 50),
        range_outline_color: Tuple[int, int, int, int] = (0, 140, 220, 140),
    ):
        """Initialize building sprite.
        
        Args:
            x: X position (used as midbottom.x)
            y: Y position (used as midbottom.y)
            image: pygame.Surface for the building
            entity_id: Unique identifier for linking to simulation entity
            range_px: Optional attack range radius to visualize
            range_fill_color: RGBA fill color for the range indicator
            range_outline_color: RGBA outline color for the range indicator
        """
        super().__init__(x, y, image, entity_id)
        self._range_surface: Optional[pygame.Surface] = None
        self._range_rect: Optional[pygame.Rect] = None
        self._range_px = range_px

        if range_px and range_px > 0:
            self._create_range_indicator(range_px, range_fill_color, range_outline_color)

    def _create_range_indicator(
        self,
        range_px: float,
        fill_color: Tuple[int, int, int, int],
        outline_color: Tuple[int, int, int, int],
    ) -> None:
        radius = int(range_px)
        diameter = radius * 2
        surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (radius, radius)

        pygame.draw.circle(surface, fill_color, center, radius)
        pygame.draw.circle(surface, outline_color, center, radius, width=2)

        self._range_surface = surface
        self._range_rect = surface.get_rect(center=(self.rect.midbottom[0], self.rect.midbottom[1]))

    def set_position(self, x: float, y: float) -> None:
        super().set_position(x, y)
        if self._range_rect is not None:
            self._range_rect.center = (x, y)

    def get_range_overlay(self) -> Optional[Tuple[pygame.Surface, pygame.Rect]]:
        if self._range_surface and self._range_rect:
            return self._range_surface, self._range_rect
        return None
