"""Map-related modules for terrain data and map rendering."""

from ..config import TILE_SIZE
from .map_data import (
    CLIFF_DEPTH,
    CLIFF_HORIZONTAL_SPACING,
    CLIFF_OVERLAP,
    CLIFF_TILE_RECTS,
    FOAM_TILE_POSITIONS,
    LEFT_PATH_POSITIONS,
    get_terrain_maps,
)
from .map_renderer import TileMap

__all__ = [
    'CLIFF_DEPTH',
    'CLIFF_HORIZONTAL_SPACING',
    'CLIFF_OVERLAP',
    'CLIFF_TILE_RECTS',
    'FOAM_TILE_POSITIONS',
    'LEFT_PATH_POSITIONS',
    'TILE_SIZE',
    'TileMap',
    'get_terrain_maps',
]
