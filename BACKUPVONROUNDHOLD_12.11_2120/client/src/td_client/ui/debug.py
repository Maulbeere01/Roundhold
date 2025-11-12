"""Debug rendering utilities (grid, coordinates, info text)."""
import logging

import pygame

from ..config.settings import GameSettings

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
    
    def toggle_grid(self) -> None:
        """Toggle grid overlay visibility."""
        self.show_grid = not self.show_grid
        logger.debug(f"Grid overlay: {'ON' if self.show_grid else 'OFF'}")
    
    def toggle_coords(self) -> None:
        """Toggle coordinate display in grid cells."""
        self.show_coords = not self.show_coords
        status = 'ON' if self.show_coords else 'OFF'
        logger.debug(f"Grid coordinates: {status}")
    
    def draw_grid(
        self,
        surface: pygame.Surface,
        center_x: int,
        left_map_width: int,
        right_map_width: int,
        vertical_offset: int
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
        
        for x in range(0, render_width, self.settings.tile_size):
            pygame.draw.line(
                grid_surface, 
                self.settings.grid_color,
                (x, 0), 
                (x, render_height),
                self.settings.grid_thickness
            )
        
        for y in range(0, render_height, self.settings.tile_size):
            pygame.draw.line(
                grid_surface,
                self.settings.grid_color,
                (0, y),
                (render_width, y),
                self.settings.grid_thickness
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
    
    def _draw_coordinate_label(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        row_pixel: int,
        col_pixel: int,
    ) -> None:
        """Draw a single coordinate label in a grid cell.
        
        Args:
            surface: Surface to draw onto
            font: Font to use for text
            row_pixel: Y pixel coordinate
            col_pixel: X pixel coordinate
        """
        abs_row = row_pixel // self.settings.tile_size
        abs_col = col_pixel // self.settings.tile_size
        coord_text = f"{abs_row},{abs_col}"
        
        text_surface = font.render(coord_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.center = (
            col_pixel + self.settings.tile_size // 2,
            row_pixel + self.settings.tile_size // 2
        )
        
        bg_rect = text_rect.inflate(4, 2)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect)
        surface.blit(text_surface, text_rect)
    
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
        
        for row_pixel in range(0, render_height, self.settings.tile_size):
            for col_pixel in range(
                0, render_width, self.settings.tile_size
            ):
                self._draw_coordinate_label(
                    surface, font, row_pixel, col_pixel
                )
    
    def draw_info_text(self, surface: pygame.Surface) -> None:
        """Draw game info overlay.
        
        Args:
            surface: Surface to draw info text onto
        """
        font = pygame.font.Font(None, 24)
        cols = self.settings.screen_width // self.settings.tile_size
        rows = self.settings.screen_height // self.settings.tile_size
        
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
