"""Map-related modules for terrain data and map rendering."""

from .map_data import (
    CLIFF_OVERLAP,
    CLIFF_TILE_RECTS,
    FOAM_TILE_POSITIONS,
    get_visual_map_from_layout,
)
from .map_renderer import TileMap

__all__ = [
    "CLIFF_OVERLAP",
    "CLIFF_TILE_RECTS",
    "FOAM_TILE_POSITIONS",
    "TileMap",
    "get_visual_map_from_layout",
]
