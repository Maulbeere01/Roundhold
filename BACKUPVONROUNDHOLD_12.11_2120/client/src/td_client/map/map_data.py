"""Map generation and tile configuration."""
import logging
from typing import Dict, List, Tuple

from ..config import (
    MAP_HEIGHT_TILES,
    MAP_WIDTH_TILES,
    TILE_RENDER_SIZE,
    TILE_SOURCE_SIZE,
)

logger = logging.getLogger(__name__)

# Tile rectangles mapping tile IDs to (x, y, width, height) in source PNG
TILE_RECTS: Dict[int, Tuple[int, int, int, int]] = {
    0: (0, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE), 

    # Left terrain tiles (3x3 border set)
    1: (0, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-left
    2: (TILE_SOURCE_SIZE, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-middle
    3: (2 * TILE_SOURCE_SIZE, 0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Top-right
    4: (0, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Mid-left
    5: (TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Center
    6: (2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Mid-right
    7: (0, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-left
    8: (TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-middle
    9: (2 * TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),  # Bottom-right
    
    # Right terrain tiles (3x3 border set, offset by 320px)
    10: (320 + 0 * TILE_SOURCE_SIZE, 0 + 0 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    11: (320 + 1 * TILE_SOURCE_SIZE, 0 + 0 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    12: (320 + 2 * TILE_SOURCE_SIZE, 0 + 0 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    13: (320 + 0 * TILE_SOURCE_SIZE, 1 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    14: (320 + 1 * TILE_SOURCE_SIZE, 1 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    15: (320 + 2 * TILE_SOURCE_SIZE, 1 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    16: (320 + 0 * TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    17: (320 + 1 * TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
    18: (320 + 2 * TILE_SOURCE_SIZE, 2 * TILE_SOURCE_SIZE, TILE_SOURCE_SIZE, TILE_SOURCE_SIZE),
}

# Elevation/cliff rendering configuration
# Source coordinates in Tilemap_Elevation.png (x, y, width, height)
CLIFF_TILE_RECTS: Dict[str, Tuple[int, int, int, int]] = {
    "base": (0, 351, 191, 33),  
    "right_edge": (192, 351, 64, 33),  # Right edge cliff tile (covers hard edge at end of map)
}

# Elevation rendering constants
CLIFF_DEPTH = 5  # Number of vertical cliff tile rows
CLIFF_OVERLAP = 93  # Pixel overlap with terrain 
CLIFF_HORIZONTAL_SPACING = 191  # spacing between cliff elements

# Cliff column positions 
# Bottom row is rendered using these static positions, plus right edge tile
CLIFF_COLUMN_POSITIONS: List[int] = list(range(MAP_WIDTH_TILES))


def _get_border_tile_key( row: int, col: int, height: int, width: int) -> str:
    """Determine tile position key based on row and column.
    
        Categorizes each tile position in a rectangular map into one of 9 possible
        border tile types based on its position relative to the map boundaries.
        This enables automatic placement of appropriate border tiles (corners, edges,
        center) when generating terrain maps.
        
        The function uses a 3x3 grid pattern:
        - Corners: top_left, top_right, bottom_left, bottom_right
        - Edges: top_mid, bottom_mid, mid_left, mid_right  
        - Center: mid_mid
    Args:
        row: Row index
        col: Column index
        height: Total map height
        width: Total map width
        
    Returns:
        Tile position key (e.g., 'top_left', 'mid_mid')

    The returned key is then used to look up the corresponding tile ID
    from LEFT_TILES or RIGHT_TILES dictionaries.
    """
    is_top = row == 0
    is_bottom = row == height - 1
    is_left = col == 0
    is_right = col == width - 1
    
    if is_top:
        return 'top_left' if is_left else (
            'top_right' if is_right else 'top_mid'
        )
    elif is_bottom:
        return 'bottom_left' if is_left else (
            'bottom_right' if is_right else 'bottom_mid'
        )
    else:
        return 'mid_left' if is_left else (
            'mid_right' if is_right else 'mid_mid'
        )


def generate_terrain_map(
    width: int,
    height: int,
    tile_ids: Dict[str, int]
) -> List[List[int]]:
    """Generate a map with border tiles.
    
    Creates a rectangular map with specific tiles for borders
    (corners, edges) and center areas, using a 3x3 tile pattern.
    
    Args:
        width: Number of tiles horizontally
        height: Number of tiles vertically
        tile_ids: Dict mapping position names to tile IDs
        
    Returns:
        2D list of tile IDs
    """
    return [
        [
            tile_ids[_get_border_tile_key(row, col, height, width)]
            for col in range(width)
        ]
        for row in range(height)
    ]


# Tile ID mappings for different terrains
LEFT_TILES = {
    'top_left': 1, 'top_mid': 2, 'top_right': 3,
    'mid_left': 4, 'mid_mid': 5, 'mid_right': 6,
    'bottom_left': 7, 'bottom_mid': 8, 'bottom_right': 9
}

RIGHT_TILES = {
    'top_left': 10, 'top_mid': 11, 'top_right': 12,
    'mid_left': 13, 'mid_mid': 14, 'mid_right': 15,
    'bottom_left': 16, 'bottom_mid': 17, 'bottom_right': 18
}

# Generate maps dynamically based on calculated dimensions
_LEFT_MAP = generate_terrain_map(
    MAP_WIDTH_TILES, MAP_HEIGHT_TILES, LEFT_TILES
)
_RIGHT_MAP = generate_terrain_map(
    MAP_WIDTH_TILES, MAP_HEIGHT_TILES, RIGHT_TILES
)


def get_terrain_maps() -> Tuple[List[List[int]], List[List[int]]]:
    return (_LEFT_MAP, _RIGHT_MAP)

# Path tile positions for left map (row, col) coordinates
# Coordinates are 0-based (matching the debug grid display and actual map coordinates)
# The Path tiles on the right get deduced from the left map by mirroring the positions
LEFT_PATH_POSITIONS: List[Tuple[int, int]] = [
    (13, 2), (13, 3), (13, 4), (12, 4), (11, 4), (11, 5), (11, 6), (11, 7), 
    (11, 8), (12, 8), (13, 8), (13, 9), (13, 10), (13, 11), (13, 12),
    (12, 12), (11, 12), (10, 12), (10, 13), (10, 14), (10, 15), (11, 15),
    (11, 16), (11, 17), (11, 18), (11, 19), (11, 20),
    (12, 1), (13, 1), (14, 1), (15, 1), (16, 1), (17, 1),
    (18, 1), (19, 1), (20, 1), (21, 1), (22, 1), (23, 1),
    (23, 2), (23, 3), (23, 4), (23, 5), (23, 6), (23, 7),
    (23, 8), (23, 9), (23, 10), (23, 11), (23, 12), (23, 13),
    (23, 14), (23, 15), (23, 16), (23, 17), (23, 18), (23, 19), (23, 20),
    (10, 1), (9, 1), (8, 1), (7, 1), (6, 1), (5, 1), (4, 1), (3, 1), (2, 1), (1, 1),
    (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11),
    (1, 12), (1, 13), (1, 14), (1, 15), (1, 16), (1, 17), (1, 18), (1, 19), (1, 20),
    (2, 12), (3, 12), (4, 12), (5, 12), (6, 12),
    (7, 12), (7, 13), (7, 14), (7, 15), (7, 16), (7, 17), (7, 18), (7, 19), (7, 20),
    (22, 7), (21, 7), (20, 7), (19, 7), (18, 7), (17, 7), (16, 7),
    (16, 8), (16, 9), (16, 10), (16, 11), (16, 12), (16, 13), (16, 14),
    (16, 15), (16, 16), (16, 17), (16, 18), (16, 19), (16, 20),
]


# Foam tile positions (row, col) where foam should appear under the map
# Only the left map is used for foam tiles, the right map is deduced from the left map by mirroring the positions
FOAM_TILE_POSITIONS: List[Tuple[int, int]] = [
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
]


logger.debug(
    f"Generated maps: {MAP_WIDTH_TILES}x{MAP_HEIGHT_TILES} tiles "
    f"(TILE_RENDER_SIZE={TILE_RENDER_SIZE})"
)
