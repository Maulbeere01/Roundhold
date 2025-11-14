# mypy: ignore-errors
"""Map generation and tile configuration."""
import logging
from typing import Dict, List, Optional, Tuple

from td_shared.map.static_map import GLOBAL_MAP_LAYOUT, TILE_TYPE_GRASS, TILE_TYPE_PATH, TILE_TYPE_WATER
from ..config import (
    TILE_SOURCE_SIZE,
)

logger = logging.getLogger(__name__)

# Tile rectangles mapping tile IDs to (x, y, width, height) in source PNG
TILE_RECTS: Dict[int, Tuple[int, int, int, int]] = {
    0: (0, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),

    # Terrain tiles (3x3 border set) - used for both left and right islands
    1: (0, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-left
    2: (TILE_SOURCE_SIZE, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-middle
    3: (2 * TILE_SOURCE_SIZE, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-right
    4: (0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Mid-left
    5: (TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Center
    6: (2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Mid-right
    7: (0, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-left
    8: (TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-middle
    9: (2 * TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-right
}

# Elevation/cliff rendering configuration
# Source coordinates in Tilemap_Elevation.png (x, y, width, height)
CLIFF_TILE_RECTS: Dict[str, Tuple[int, int, int, int]] = {
    "base": (0, 351, 191, 33),
    "right_edge": (192, 351, 64, 33),  # Right edge cliff tile (covers hard edge at end of map)
}

# Elevation rendering constants
CLIFF_OVERLAP = 92  # Pixel overlap with terrain


def _get_smart_tile_id(row: int, col: int) -> int:
    """Determine the correct tile ID based on position relative to the two islands.

    Uses 3x3 autotile logic to determine border tiles:
    - Left Island: columns 0-21
    - Right Island: columns 24-45
    - Water gap: columns 22-23 (should not call this function for water)
    - Rows: 0-24

    Args:
        row: Row index (0-24)
        col: Column index (0-45)

    Returns:
        Tile ID (1-9) for the appropriate border/center tile
    """
    # Determine which island this tile belongs to
    is_left_island = 0 <= col <= 21
    is_right_island = 24 <= col <= 45

    # Border detection relative to the island boundaries
    is_top = (row == 0)
    is_bottom = (row == 24)

    if is_left_island:
        is_left = (col == 0)
        is_right = (col == 21)
    elif is_right_island:
        is_left = (col == 24)
        is_right = (col == 45)
    else:
        return 5

    # Determine tile ID using 3x3 autotile logic
    if is_top:
        if is_left:
            return 1  # Top-left
        elif is_right:
            return 3  # Top-right
        else:
            return 2  # Top-middle
    elif is_bottom:
        if is_left:
            return 7  # Bottom-left
        elif is_right:
            return 9  # Bottom-right
        else:
            return 8  # Bottom-middle
    else:
        if is_left:
            return 4  # Mid-left
        elif is_right:
            return 6  # Mid-right
        else:
            return 5  # Center


def get_visual_map_from_layout() -> List[List[Optional[int]]]:
    """Generate visual map from GLOBAL_MAP_LAYOUT.

    Converts the static map layout to visual tile IDs:
    - 0 (Grass) -> Smart tile ID (1-9) based on border position
    - 1 (Path) -> Smart tile ID (1-9) based on border position (paths are overlays, base is grass)
    - 2 (Water) -> None (transparent, background water shows through)

    Returns:
        2D list of visual tile IDs (int) or None for water tiles
    """
    visual_map = []
    for row_idx, row in enumerate(GLOBAL_MAP_LAYOUT):
        visual_row = []
        for col_idx, tile_type in enumerate(row):
            if tile_type == TILE_TYPE_WATER:
                # Water tiles - return None for transparency
                visual_row.append(None)
            elif tile_type == TILE_TYPE_GRASS or tile_type == TILE_TYPE_PATH:
                # Both grass and paths use smart tile ID based on position
                # Paths are overlays, so base terrain still needs proper borders
                tile_id = _get_smart_tile_id(row_idx, col_idx)
                visual_row.append(tile_id)
            else:
                visual_row.append(5)
        visual_map.append(visual_row)
    return visual_map



# Foam tile positions (row, col) where foam should appear under the map
FOAM_TILE_POSITIONS: List[Tuple[int, int]] = [
    # Left island (columns 0-21)
    (24, 0),
    (24, 1),
    (24, 2),
    (24, 3),
    (24, 4),
    (24, 5),
    (24, 6),
    (24, 7),
    (24, 8),
    (24, 9),
    (24, 10),
    (24, 11),
    (24, 12),
    (24, 13),
    (24, 14),
    (24, 15),
    (24, 16),
    (24, 17),
    (24, 18),
    (24, 19),
    (24, 20),
    (24, 21),
    # Right island (columns 24-45)
    (24, 24),
    (24, 25),
    (24, 26),
    (24, 27),
    (24, 28),
    (24, 29),
    (24, 30),
    (24, 31),
    (24, 32),
    (24, 33),
    (24, 34),
    (24, 35),
    (24, 36),
    (24, 37),
    (24, 38),
    (24, 39),
    (24, 40),
    (24, 41),
    (24, 42),
    (24, 43),
    (24, 44),
    (24, 45),
]
