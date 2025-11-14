"""TileMap rendering with elevation layers."""

from typing import TYPE_CHECKING

import pygame
from td_shared.game import TILE_SIZE_PX

from ..rendering.elevation_renderer import ElevationRenderer
from .map_data import TILE_RECTS

if TYPE_CHECKING:
    from ..assets.loader import AssetLoader


class TileMap:
    """Tilemap for rendering 2D grid of tiles using a tileset

    Renders a static map from tile data
    Provides image and rect attributes for direct rendering
    """

    def __init__(
        self,
        tile_map: list[list[int | None]],
        tileset_surface: pygame.Surface,
        offset_x: int = 0,
        offset_y: int = 0,
        asset_loader: "AssetLoader" = None,
    ):
        """Init tilemap

        Args:
            tile_map: 2D list of tile IDs
            tileset_surface: Tileset surface for rendering tiles
            offset_x: Horizontal position offset
            offset_y: Vertical position offset
            asset_loader: AssetLoader for rendering cliff walls
        """

        self.tileset = tileset_surface
        self.tile_map = tile_map

        map_width = len(tile_map[0]) * TILE_SIZE_PX
        map_height = len(tile_map) * TILE_SIZE_PX

        self.image = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        self._build_map()

        self.elevation_renderer = ElevationRenderer(
            asset_loader, TILE_SIZE_PX, map_width, map_height
        )

        self.rect = self.image.get_rect()
        self.rect.x = offset_x
        self.rect.y = offset_y

    def get_elevation_surface(self) -> pygame.Surface:
        return self.elevation_renderer.get_surface()

    def get_elevation_offset(self) -> tuple:
        return self.elevation_renderer.get_offset()

    def _build_map(self):
        """Build the map surface from tile data by blitting tiles."""
        for row, row_data in enumerate(self.tile_map):
            for col, tile_id in enumerate(row_data):
                # Skip None tiles (water) - they remain transparent
                if tile_id is None:
                    continue

                rect = TILE_RECTS.get(tile_id)
                if rect:
                    tile_rect = pygame.Rect(rect)
                    tile_surface = self.tileset.subsurface(tile_rect)

                    if TILE_SIZE_PX != tile_rect.width:
                        tile_surface = pygame.transform.scale(
                            tile_surface, (TILE_SIZE_PX, TILE_SIZE_PX)
                        )

                    self.image.blit(
                        tile_surface, (col * TILE_SIZE_PX, row * TILE_SIZE_PX)
                    )
