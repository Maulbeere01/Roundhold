"""Debug rendering utilities (grid, coordinates, info text)."""
import logging

import pygame

from ..config import GameSettings
from td_shared.map import PlacementGrid, GridCellState
from td_shared.game import MAP_WIDTH_TILES

logger = logging.getLogger(__name__)


class DebugRenderer:
    """Handles debug rendering overlays.
    
    Provides visualization tools for development including grid overlay,
    coordinate display, and runtime information.
    """
    
    def __init__(self, settings: GameSettings):
        """Initialize debug renderer with game settings.
        
        Args:
            settings: GameSettings instance
        """
        self.settings = settings
        self.show_grid = settings.show_grid
        self.show_coords = settings.show_grid_coords
        self.show_info = False
    
    def toggle_grid(self) -> None:
        self.show_grid = not self.show_grid
        self.show_coords = self.show_grid
        self.show_info = self.show_grid
    
    def draw_grid(
        self,
        surface: pygame.Surface,
        center_x: int,
        left_map_width: int,
        right_map_width: int,
        vertical_offset: int,
        placement_grid_left: PlacementGrid | None = None,
        placement_grid_right: PlacementGrid | None = None,
        left_origin: tuple[int, int] | None = None,
        right_origin: tuple[int, int] | None = None,
    ) -> None:
        """Draw grid overlay with optional coordinates.
        
        Args:
            surface: Surface to draw grid onto
            center_x: X coordinate of center divider
            left_map_width: Width of left map in pixels
            right_map_width: Width of right map in pixels
            vertical_offset: Vertical offset of maps
        """
        if not self.show_grid:
            return
        
        render_width, render_height = surface.get_size()
        grid_surface = pygame.Surface((render_width, render_height), pygame.SRCALPHA)

        if placement_grid_left is not None and left_origin is not None:
            self._draw_single_grid(
                grid_surface, placement_grid_left, left_origin[0], left_origin[1]
            )
        if placement_grid_right is not None and right_origin is not None:
            self._draw_single_grid(
                grid_surface, placement_grid_right, right_origin[0], right_origin[1]
            )
        
        if self.show_coords:
            self._draw_coordinates(
                grid_surface,
                center_x,
                left_map_width,
                right_map_width,
                vertical_offset,
                render_width,
                render_height
            )
        
        surface.blit(grid_surface, (0, 0))
    
    def _draw_single_grid(
        self,
        surface: pygame.Surface,
        grid: PlacementGrid,
        origin_x: int,
        origin_y: int,
        *,
        mirror_x: bool = False,
        map_width_pixels: int | None = None,
    ) -> None:
        tile = self.settings.tile_size
        for r in range(grid.height_tiles):
            for c in range(grid.width_tiles):
                state = grid.grid[r][c]
                if state == GridCellState.EMPTY:
                    continue
                # Compute screen position
                if mirror_x and map_width_pixels is not None:
                    # Mirror column within the right map
                    draw_col = (grid.width_tiles - 1 - c)
                else:
                    draw_col = c
                x = origin_x + draw_col * tile
                y = origin_y + r * tile
                rect = pygame.Rect(x, y, tile, tile)
                if state == GridCellState.PATH:
                    color = (50, 100, 200, 70)
                elif state == GridCellState.OCCUPIED:
                    color = (220, 60, 60, 100)
                else:
                    color = (0, 0, 0, 0)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (255, 255, 255, 40), rect, 1)
    
    
    def _draw_coordinates(
        self,
        surface: pygame.Surface,
        center_x: int,
        left_map_width: int,
        right_map_width: int,
        vertical_offset: int,
        render_width: int,
        render_height: int
    ) -> None:
        """Draw row,col coordinates in each grid cell.
        
        Args:
            surface: Surface to draw coordinates onto
            center_x: X coordinate of center divider
            left_map_width: Width of left map in pixels
            right_map_width: Width of right map in pixels
            vertical_offset: Vertical offset of maps
            render_width: Total render width
            render_height: Total render height
        """
        font = pygame.font.Font(
            None, max(16, self.settings.tile_size // 3)
        )
        
        for row_pixel in range(0, render_height - self.settings.tile_size, self.settings.tile_size):
            for col_pixel in range(
                0, render_width, self.settings.tile_size
            ):
                # Calculate actual map coordinates (0-based)
                # Account for vertical_offset: map starts at y=vertical_offset
                if row_pixel >= vertical_offset:
                    map_row = (row_pixel - vertical_offset) // self.settings.tile_size
                else:
                    continue
                
                # For columns, need to account for map offsets
                # Left map starts at center_x - left_map_width - TILE_SIZE
                # Right map starts at center_x + TILE_SIZE
                left_map_start_x = center_x - left_map_width - self.settings.tile_size
                right_map_start_x = center_x + self.settings.tile_size
                
                # Determine map-local column and which side we're on
                on_left_map = False
                if left_map_start_x <= col_pixel < left_map_start_x + left_map_width:
                    on_left_map = True
                    map_col = (col_pixel - left_map_start_x) // self.settings.tile_size
                elif right_map_start_x <= col_pixel < right_map_start_x + right_map_width:
                    map_col = (col_pixel - right_map_start_x) // self.settings.tile_size
                else:
                    continue
                
                # - Right map columns are mirrored
                sim_row = map_row
                if on_left_map:
                    sim_col = map_col
                else:
                    sim_col = (MAP_WIDTH_TILES - 1 - map_col)
                
                # Draw coordinate labels using simulation coordinates
                coord_text = f"{sim_row},{sim_col}"
                text_surface = font.render(coord_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect()
                text_rect.center = (
                    col_pixel + self.settings.tile_size // 2,
                    row_pixel + self.settings.tile_size // 2
                )
                
                bg_rect = text_rect.inflate(4, 2)
                pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect)
                surface.blit(text_surface, text_rect)
    
    def draw_info_text(self, surface: pygame.Surface) -> None:
        """Draw game info overlay.
        
        Args:
            surface: Surface to draw info text onto
        """
        if not self.show_info:
            return
        
        font = pygame.font.Font(None, 24)
        surface_width, surface_height = surface.get_size()
        cols = surface_width // self.settings.tile_size
        rows = surface_height // self.settings.tile_size
        
        tile_size = self.settings.tile_render_size
        info_lines = [
            f"TILE_RENDER_SIZE: {tile_size}x{tile_size}",
            f"Grid: {cols}x{rows} cells",
            "Press 'G' to toggle grid",
        ]
        
        y_offset = 10
        for line in info_lines:
            text_surface = font.render(
                line, True, (255, 255, 255)
            )
            bg_rect = text_surface.get_rect()
            bg_rect.topleft = (10, y_offset)
            bg_rect.width += 10
            bg_rect.height += 4
            
            pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
            surface.blit(text_surface, (10, y_offset))
            y_offset += 25
