from __future__ import annotations

from ..game.game_balance import (
    TILE_SIZE_PX,
    ZONE_BOUNDARY_LEFT,
    ZONE_BOUNDARY_RIGHT,
)
from .grid_defs import GridCellState
from .static_map import TILE_TYPE_GRASS, TILE_TYPE_PATH


class PlacementGrid:
    """Logical grid for build validation"""

    def __init__(self, layout: list[list[int]]) -> None:
        self.height_tiles = len(layout)
        self.width_tiles = len(layout[0])
        self.grid: list[list[GridCellState]] = [
            [GridCellState.EMPTY for _ in range(self.width_tiles)]
            for _ in range(self.height_tiles)
        ]
        self._populate_from_layout(layout)

    def _populate_from_layout(self, layout: list[list[int]]) -> None:
        """Mark all non-grass tiles as blocked based on the static map layout."""
        for row_idx, row in enumerate(layout):
            for col_idx, tile_type in enumerate(row):
                if tile_type == TILE_TYPE_GRASS:
                    continue
                if tile_type == TILE_TYPE_PATH:
                    self.grid[row_idx][col_idx] = GridCellState.PATH
                else:
                    self.grid[row_idx][col_idx] = GridCellState.BLOCKED

    def is_buildable(self, row: int, col: int) -> bool:
        if not (0 <= row < self.height_tiles and 0 <= col < self.width_tiles):
            return False
        return self.grid[row][col] == GridCellState.EMPTY

    def validate_build(self, player_id: str, row: int, col: int) -> bool:
        """Check both physical availability and zone ownership for a build action."""
        if not self.is_buildable(row, col):
            return False

        if player_id == "A":
            return col <= ZONE_BOUNDARY_LEFT
        if player_id == "B":
            return col >= ZONE_BOUNDARY_RIGHT

        return False

    def place_tower(self, row: int, col: int) -> bool:
        if self.is_buildable(row, col):
            self.grid[row][col] = GridCellState.OCCUPIED
            return True
        return False

    def clear_tower(self, row: int, col: int) -> None:
        if 0 <= row < self.height_tiles and 0 <= col < self.width_tiles:
            if self.grid[row][col] == GridCellState.OCCUPIED:
                self.grid[row][col] = GridCellState.EMPTY

    def pixel_to_grid_coords(self, pixel_x: float, pixel_y: float) -> tuple[int, int]:
        row = int(pixel_y // TILE_SIZE_PX)
        col = int(pixel_x // TILE_SIZE_PX)
        return row, col
