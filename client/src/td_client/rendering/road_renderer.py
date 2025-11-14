"""Road renderer for rendering paths/roads over maps."""

import pygame


class RoadRenderer:
    """Renders paths/roads over map"""

    def __init__(
        self,
        path_tile_image: pygame.Surface,
        tile_size: int,
        map_width: int,
        map_cols: int,
        map_offset_x: int,
        map_offset_y: int,
        screen_width: int,
        screen_height: int,
    ):
        """
        Args:
            path_tile_image: Surface for a single path tile
            tile_size: Size of a tile in pixels
            map_width: Width of map in pixels
            map_cols: Number of columns in map
            map_offset_x: X offset of map
            map_offset_y: Y offset of map
            screen_width: Screen width
            screen_height: Screen height
        """
        self.path_tile_image = path_tile_image
        self.tile_size = tile_size
        self.map_width = map_width
        self.map_cols = map_cols
        self.map_offset_x = map_offset_x
        self.map_offset_y = map_offset_y
        self.screen_width = screen_width
        self.screen_height = screen_height

        if self.path_tile_image.get_size() != (tile_size, tile_size):
            self.path_tile_image = pygame.transform.scale(
                self.path_tile_image, (tile_size, tile_size)
            )

        self.path_overlay = None
        self._path_positions: list[tuple[int, int]] = []

    def set_paths(self, path_positions: list[tuple[int, int]]) -> None:
        """Set path positions and create overlay

        Args:
            path_positions: List of (tile_row, tile_col) tuples in global coordinates
        """
        self._path_positions = path_positions
        self._build_overlay()

    def _build_overlay(self) -> None:
        """Build the path overlay surface."""
        path_surface = pygame.Surface(
            (self.screen_width, self.screen_height), pygame.SRCALPHA
        )

        for tile_row, tile_col in self._path_positions:
            x = self.map_offset_x + (tile_col * self.tile_size)
            y = self.map_offset_y + (tile_row * self.tile_size)

            path_surface.blit(self.path_tile_image, (x, y))

        self.path_overlay = path_surface

    def get_overlay(self) -> pygame.Surface:
        return self.path_overlay
