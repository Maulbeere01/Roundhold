from typing import Dict, List, Tuple, TypedDict

# Global round/game pacing
DEFAULT_TICK_RATE: int = 20
PREP_SECONDS: float = 10.0
COMBAT_SECONDS: float = 120.0

PLAYER_A: str = "A"
PLAYER_B: str = "B"

# Networking/round sync
ROUND_ACK_TIMEOUT: float = 120.0

# Player economy
PLAYER_LIVES: int = 20
START_GOLD: int = 50
GOLD_PER_KILL: int = 1

class UnitStats(TypedDict):
    cost: int
    health: int
    speed: float


class TowerStats(TypedDict):
    cost: int
    damage: int
    range_px: float
    cooldown_ticks: int

UNIT_STATS: Dict[str, UnitStats] = {
    "standard": {
        "cost": 5,
        "health": 50,
        "speed": 120.0,
    },
}

TOWER_STATS: Dict[str, TowerStats] = {
    "standard": {
        "cost": 20,
        "damage": 25,
        "range_px": 120.0,
        "cooldown_ticks": 10,
    },
}

# Map geometry and paths

# Tile size in pixels (used by both server and client)
TILE_SIZE_PX = 40

# Map dimensions
MAP_WIDTH_TILES = 22


def tile_to_pixel(row: int, col: int) -> Tuple[float, float]:
    """Convert tile coordinates (row, col) to pixel coordinates (x, y).
    
    Args:
        row: Row index (0-based)
        col: Column index (0-based)
        
    Returns:
        Tuple of (x, y) pixel coordinates
    """
    return (float(col * TILE_SIZE_PX), float(row * TILE_SIZE_PX))


# Game path definitions.
# Paths are stored as lists of (row, col) tile coordinates (0-based).
#  The client is responsible for any mirroring or translation required for display.
GAME_PATHS: Dict[int, List[Tuple[int, int]]] = {
    1: [
        # Route 1
        (1, 21), (1, 20), (1, 19), (1, 18), (1, 17), (1, 16), (1, 15), (1, 14), (1, 13), (1, 12),
        (1, 11), (1, 10), (1, 9), (1, 8), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3),
        (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2),
    ],
    2: [
        # Route 2 
        (7, 21), (7, 20), (7, 19), (7, 18), (7, 17), (7, 16), (7, 15), (7, 14),
        (7, 13), (6, 13), (5, 13), (4, 13), (3, 13), (2, 13), (1, 13),
        (1, 12), (1, 11), (1, 10), (1, 9), (1, 8), (1, 7), (1, 6), (1, 5), (1, 4), (1, 3),
        (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2),
    ],
    3: [
        # Route 3 
        (11, 21), (11, 20), (11, 19), (11, 18), (11, 17), (11, 16),
        (10, 16), (10, 15), (10, 14), (10, 13), (11, 13), (12, 13), (13, 13),
        (13, 12), (13, 11), (13, 10), (13, 9), (12, 9),
        (11, 9), (11, 8), (11, 7), (11, 6), (11, 5), (12, 5), (13, 5), (13, 4), (13, 3), (13, 2), (12, 2),
    ],
    4: [
        # Route 4 
        (16, 21), (16, 20), (16, 19), (16, 18), (16, 17), (16, 16), (16, 15), (16, 14), (16, 13), (16, 12), (16, 11), (16, 10), (16, 9),
        (16, 8), (17, 8), (18, 8), (19, 8), (20, 8), (21, 8), (22, 8),
        (23, 8), (23, 7), (23, 6), (23, 5), (23, 4), (23, 3),
        (23, 2), (22, 2), (21, 2), (20, 2), (19, 2), (18, 2), (17, 2), (16, 2), (15, 2), (14, 2), (13, 2), (12, 2),
    ],
    5: [
        # Route 5
        (23, 21), (23, 20), (23, 19), (23, 18), (23, 17), (23, 16), (23, 15), (23, 14), (23, 13), (23, 12), (23, 11), (23, 10), (23, 9),
        (23, 8), (23, 7), (23, 6), (23, 5), (23, 4), (23, 3),
        (23, 2), (22, 2), (21, 2), (20, 2), (19, 2), (18, 2), (17, 2), (16, 2), (15, 2), (14, 2), (13, 2), (12, 2),
    ],
}
