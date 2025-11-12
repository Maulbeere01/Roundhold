"""TileMap rendering with elevation layers."""
import pygame
from typing import List, Optional

from ..config import TILE_SIZE
from ..rendering.elevation_renderer import ElevationRenderer
from .map_data import TILE_RECTS


class TileMap:
    """Tilemap for rendering 2D grid of tiles using a tileset
    
    Renders a static map from tile data 
    Provides image and rect attributes for direct rendering
    """
    
    def __init__(
        self,
        tile_map: List[List[int]],
        tileset_surface: pygame.Surface,
        offset_x: int = 0,
        offset_y: int = 0,
        elevation_tileset: Optional[pygame.Surface] = None
    ):
        """Init tilemap 
        
        Args:
            tile_map: 2D list of tile IDs
            tileset_surface: Tileset surface for rendering tiles
            offset_x: Horizontal position offset
            offset_y: Vertical position offset
            elevation_tileset: Optional tileset for rendering cliff walls
        """
        
        self.tileset = tileset_surface
        self.tile_map = tile_map
        
        map_width = len(tile_map[0]) * TILE_SIZE
        map_height = len(tile_map) * TILE_SIZE
        
        self.image = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        self._build_map()
        
        self.elevation_renderer: Optional[ElevationRenderer] = None
        if elevation_tileset is not None:
            self.elevation_renderer = ElevationRenderer(
                elevation_tileset,
                TILE_SIZE,
                map_width,
                map_height
            )
        
        self.rect = self.image.get_rect()
        self.rect.x = offset_x
        self.rect.y = offset_y
    
    def get_elevation_surface(self) -> Optional[pygame.Surface]:
        if self.elevation_renderer:
            return self.elevation_renderer.get_surface()
        return None
    
    def get_elevation_offset(self) -> tuple:
        if self.elevation_renderer:
            return self.elevation_renderer.get_offset()
        return (0, 0)
    
    def _build_map(self):
        """Build the map surface from tile data by blitting tiles."""
        for row, row_data in enumerate[List[int]](self.tile_map):
            for col, tile_id in enumerate[int](row_data):
                rect = TILE_RECTS.get(tile_id)
                if rect:
                    tile_rect = pygame.Rect(rect)
                    tile_surface = self.tileset.subsurface(tile_rect)
                    
                    if TILE_SIZE != tile_rect.width:
                        tile_surface = pygame.transform.scale(
                            tile_surface, (TILE_SIZE, TILE_SIZE)
                        )
                    
                    self.image.blit(
                        tile_surface,
                        (col * TILE_SIZE, row * TILE_SIZE)
                    )
