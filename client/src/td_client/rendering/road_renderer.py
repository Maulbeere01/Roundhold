"""Road renderer for rendering paths/roads over maps."""
from typing import List, Tuple

import pygame


class RoadRenderer:
    """Renders paths/roads over map"""
    
    def __init__(
        self,
        path_tile_image: pygame.Surface,
        tile_size: int,
        left_map_width: int,
        left_map_cols: int,
        map_offset_x: int,
        map_offset_y: int,
        screen_width: int,
        screen_height: int
    ):
        """
        Args:
            path_tile_image: Surface for a single path tile
            tile_size: Size of a tile in pixels
            left_map_width: Width of left map in pixels
            left_map_cols: Number of columns in left map
            map_offset_x: X offset of left map
            map_offset_y: Y offset of maps
            screen_width: Screen width
            screen_height: Screen height
        """
        self.path_tile_image = path_tile_image
        self.tile_size = tile_size
        self.left_map_width = left_map_width
        self.left_map_cols = left_map_cols
        self.map_offset_x = map_offset_x
        self.map_offset_y = map_offset_y
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        if self.path_tile_image.get_size() != (tile_size, tile_size):
            self.path_tile_image = pygame.transform.scale(
                self.path_tile_image, 
                (tile_size, tile_size)
            )
        
        self.path_overlay = None
        self._path_positions: List[Tuple[int, int]] = []
    
    def set_paths(self, path_positions: List[Tuple[int, int]]) -> None:
        """Set path positions and create overlay
        
        Args:
            path_positions: List of (tile_row, tile_col) tuples
        """
        self._path_positions = path_positions
        self._build_overlay()
    
    def mirror_paths(self, left_path_positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Mirror path positions from left to right side.
        
        Uses horizontal mirroring: right_col = left_map_cols + (left_map_cols - 1 - col)
        
        Args:
            left_path_positions: List of (tile_row, tile_col) tuples for left side
            
        Returns:
            List of mirrored positions for right side
        """
        right_path_positions = []
        for row, col in left_path_positions:
            mirrored_col = self.left_map_cols + (self.left_map_cols - 1 - col)
            right_path_positions.append((row, mirrored_col))
        return right_path_positions
    
    def _build_overlay(self) -> None:
        """Build the path overlay surface."""
        path_surface = pygame.Surface(
            (self.screen_width, self.screen_height), 
            pygame.SRCALPHA
        )
        
        for tile_row, tile_col in self._path_positions:
            if tile_col < self.left_map_cols:
                x = self.map_offset_x + (tile_col * self.tile_size)
            else:
                rel_col = tile_col - self.left_map_cols
                x = self.map_offset_x + self.left_map_width + (rel_col * self.tile_size)
            
            y = self.map_offset_y + (tile_row * self.tile_size)
            
            path_surface.blit(self.path_tile_image, (x, y))
        
        self.path_overlay = path_surface
    
    def get_overlay(self) -> pygame.Surface:
        return self.path_overlay
