from __future__ import annotations

from typing import Dict, List, Tuple

from ..game.game_balance import TILE_SIZE_PX
from .grid_defs import GridCellState


class PlacementGrid:
    """Logical grid for build validation"""

    def __init__(self, width_tiles: int, height_tiles: int) -> None:
        self.width_tiles = int(width_tiles)
        self.height_tiles = int(height_tiles)
        self.grid: List[List[GridCellState]] = [
            [GridCellState.EMPTY for _ in range(self.width_tiles)]
            for _ in range(self.height_tiles)
        ]

    def populate_from_paths(self, all_paths: Dict[int, List[Tuple[int, int]]]) -> None:
        for _, path in all_paths.items():
            for row, col in path:
                if 0 <= row < self.height_tiles and 0 <= col < self.width_tiles:
                    self.grid[row][col] = GridCellState.PATH

    def is_buildable(self, row: int, col: int) -> bool:
        if not (0 <= row < self.height_tiles and 0 <= col < self.width_tiles):
            return False
        return self.grid[row][col] == GridCellState.EMPTY

    def place_tower(self, row: int, col: int) -> bool:
        if self.is_buildable(row, col):
            self.grid[row][col] = GridCellState.OCCUPIED
            return True
        return False

    def clear_tower(self, row: int, col: int) -> None:
        if 0 <= row < self.height_tiles and 0 <= col < self.width_tiles:
            if self.grid[row][col] == GridCellState.OCCUPIED:
                self.grid[row][col] = GridCellState.EMPTY

    def pixel_to_grid_coords(self, pixel_x: float, pixel_y: float) -> Tuple[int, int]:
        row = int(pixel_y // TILE_SIZE_PX)
        col = int(pixel_x // TILE_SIZE_PX)
        return row, col


