"""Elevation renderer for cliff/rock walls under map edges."""
from typing import Tuple

import pygame

from ..map.map_data import (
    CLIFF_COLUMN_POSITIONS,
    CLIFF_DEPTH,
    CLIFF_HORIZONTAL_SPACING,
    CLIFF_OVERLAP,
    CLIFF_TILE_RECTS,
)


class ElevationRenderer:
    """Renders cliff walls beneath the bottom row of the map"""
    
    def __init__(
        self,
        elevation_tileset: pygame.Surface,
        tile_size: int,
        map_width: int,
        map_height: int
    ):
        """
        Args:
            elevation_tileset: Tileset surface for cliff tiles
            tile_size: Rendered tile size in pixels
            map_width: Total map width in pixels
            map_height: Total map height in pixels
        """
        self.elevation_tileset = elevation_tileset
        self.tile_size = tile_size
        self.map_width = map_width
        self.map_height = map_height
        
        self._load_and_scale_cliff_tiles()
        self.elevation_surface = self._build_elevation_surface()
    
    def _load_and_scale_cliff_tiles(self) -> None:
        """Load and scale cliff tiles to match tile size."""
        self.cliff_tile = self._extract_cliff_tile("base")
        self.cliff_right_edge_tile = self._extract_cliff_tile("right_edge")
        
        original_width, original_height = (
            self.cliff_tile.get_size()
        )
        scale_factor = self.tile_size / original_height
        scaled_width = int(original_width * scale_factor)
        
        self.cliff_tile = pygame.transform.scale(
            self.cliff_tile, (scaled_width, self.tile_size)
        )
        
        right_edge_original = self.cliff_right_edge_tile.get_size()
        right_edge_scaled_width = int(
            right_edge_original[0] * scale_factor
        )
        self.cliff_right_edge_tile = pygame.transform.scale(
            self.cliff_right_edge_tile,
            (right_edge_scaled_width, self.tile_size)
        )
        
        self.cliff_right_edge_width = right_edge_scaled_width
    
    def _extract_cliff_tile(self, tile_type: str) -> pygame.Surface:
        """Extract and return cliff tile from tileset.
        
        Args:
            tile_type: Type of cliff tile ("base" or "right_edge")
            
        Returns:
            Extracted tile surface
        """
        rect = CLIFF_TILE_RECTS[tile_type]
        x, y, w, h = rect
        
        tile_rect = pygame.Rect(x, y, w, h)
        tile = self.elevation_tileset.subsurface(tile_rect).copy()
        
        try:
            return tile.convert_alpha()
        except pygame.error:
            return tile
    
    def _render_cliff_column(
        self, surface: pygame.Surface, col: int, y_start: int
    ) -> None:
        """Render a vertical column of cliff tiles.
        
        Args:
            surface: Surface to render onto
            col: Column index
            y_start: Starting Y coordinate
        """
        x = col * (self.tile_size + CLIFF_HORIZONTAL_SPACING)
        
        for i in range(CLIFF_DEPTH):
            y = y_start + (i * self.tile_size)
            surface.blit(self.cliff_tile, (x, y))
    
    def _render_right_edge(self, surface: pygame.Surface, y_start: int) -> None:
        """Render cliff tiles on the right edge to cover hard edge.
        
        Args:
            surface: Surface to render onto
            y_start: Starting Y coordinate
        """
        right_edge_x = self.map_width - self.cliff_right_edge_width
        
        for i in range(CLIFF_DEPTH):
            y = y_start + (i * self.tile_size)
            surface.blit(self.cliff_right_edge_tile, (right_edge_x, y))
    
    def _build_elevation_surface(self) -> pygame.Surface:
        """Build and return pre-rendered elevation surface.
        
        Renders cliff tiles at static column positions along the bottom row,
        plus right edge to cover hard edge at end of map.
        
        Returns:
            Surface containing rendered cliff walls
        """
        cliff_height = CLIFF_DEPTH * self.tile_size
        elevation_surface = pygame.Surface(
            (self.map_width, self.map_height + cliff_height),
            pygame.SRCALPHA
        )
        
        y_start = self.map_height - CLIFF_OVERLAP
        
        # Render cliffs at static column positions
        for col in CLIFF_COLUMN_POSITIONS:
            self._render_cliff_column(elevation_surface, col, y_start)
        
        # Render right edge to cover hard edge at end of map
        self._render_right_edge(elevation_surface, y_start)
        
        return elevation_surface
    
    def get_surface(self) -> pygame.Surface:
        """Return the pre-rendered elevation surface"""
        return self.elevation_surface
    
    def get_offset(self) -> Tuple[int, int]:
        return (0, -CLIFF_OVERLAP)
