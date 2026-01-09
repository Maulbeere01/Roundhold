from __future__ import annotations

from enum import Enum


class GridCellState(Enum):
    EMPTY = 0  # Buildable terrain
    PATH = 1  # Enemy route (static)
    OCCUPIED = 2  # Tower built (dynamic)
    BLOCKED = 3  # Terrain obstacle (water/rocks)
