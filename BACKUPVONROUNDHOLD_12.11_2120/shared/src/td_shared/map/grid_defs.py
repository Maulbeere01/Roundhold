from __future__ import annotations

from enum import Enum


class GridCellState(Enum):
    EMPTY = 0
    PATH = 1
    OCCUPIED = 2


