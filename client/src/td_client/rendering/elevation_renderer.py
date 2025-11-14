"""Elevation renderer for cliff/rock walls under map edges."""

import pygame

from ..assets.loader import AssetLoader
from ..map.map_data import CLIFF_OVERLAP, CLIFF_TILE_RECTS


class ElevationRenderer:
    """Renders cliff walls beneath the bottom row of the map."""

    def __init__(
        self, asset_loader: AssetLoader, tile_size: int, map_width: int, map_height: int
    ):
        """Initialize elevation renderer.

        Args:
            asset_loader: AssetLoader instance for loading elevation tileset
            tile_size: Size of tiles in pixels
            map_width: Total map width in pixels
            map_height: Total map height in pixels
        """
        self.asset_loader = asset_loader
        self.tile_size = tile_size
        self.map_width = map_width
        self.map_height = map_height

        self._load_assets()
        self.elevation_surface = self._build_manual_surface()

    def _load_assets(self) -> None:
        """Load and scale cliff tile assets using AssetLoader."""
        # Load elevation tileset using AssetLoader
        elevation_tileset = self.asset_loader.load_image(
            self.asset_loader.paths.tileset_elevation
        )

        # 1. Extract and scale Base Wall tile
        rect_base = pygame.Rect(CLIFF_TILE_RECTS["base"])
        base_img = elevation_tileset.subsurface(rect_base).copy()

        # Scale height to tile_size (e.g. 33px -> tile_size)
        scale = self.tile_size / base_img.get_height()
        new_w = int(base_img.get_width() * scale)
        self.cliff_base = pygame.transform.scale(base_img, (new_w, self.tile_size))

        # 2. Extract and scale Edge Cap tile
        rect_edge = pygame.Rect(CLIFF_TILE_RECTS["right_edge"])
        edge_img = elevation_tileset.subsurface(rect_edge).copy()

        new_edge_w = int(edge_img.get_width() * scale)
        self.cliff_edge = pygame.transform.scale(edge_img, (new_edge_w, self.tile_size))
        self.edge_width = new_edge_w

    def _build_manual_surface(self) -> pygame.Surface:
        """Build elevation surface with cliff walls"""
        # Create canvas (map + depth for cliff)
        depth = 5
        total_h = self.map_height + (depth * self.tile_size)
        surf = pygame.Surface((self.map_width, total_h), pygame.SRCALPHA)

        y_start = self.map_height - CLIFF_OVERLAP

        # Hardcoded for simplicity
        # Where should normal wall pieces be placed (X coordinates)?
        # The asset is approximately 230px wide. We place them side by side.
        base_walls_x = [
            # Left island (start at 0)
            0,
            230,
            420,
            610,
            # Right island (start at 960)
            960,
            1190,
            1420,
            1650,
        ]

        # Where should the end pieces be placed? They cover the hard edge at the end of the map.
        edge_caps_x = [880 - self.edge_width, 1840 - self.edge_width]

        # Draw Base Walls
        for x in base_walls_x:
            for i in range(depth):
                y = y_start + (i * self.tile_size)
                surf.blit(self.cliff_base, (x, y))

        # Draw Edge Caps
        for x in edge_caps_x:
            for i in range(depth):
                y = y_start + (i * self.tile_size)
                surf.blit(self.cliff_edge, (x, y))

        return surf

    def get_surface(self) -> pygame.Surface:
        return self.elevation_surface

    def get_offset(self) -> tuple[int, int]:
        return (0, -CLIFF_OVERLAP)
