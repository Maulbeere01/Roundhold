"""Shared game definitions and simulation core.

This package contains code that is shared between the server and client,
including game data definitions and deterministic simulation logic.
"""

from .game import (
    COMBAT_SECONDS,
    GAME_PATHS,
    MAP_WIDTH_TILES,
    PLAYER_LIVES,
    PREP_SECONDS,
    START_GOLD,
    TILE_SIZE_PX,
    TOWER_STATS,
    UNIT_STATS,
    PlayerID,
    RoundResultData,
    RoundStartData,
    SimTowerData,
    SimulationData,
    SimUnitData,
    TowerStats,
    UnitStats,
    tile_to_pixel,
)
from .map import PlacementGrid
from .map.static_map import GLOBAL_MAP_LAYOUT
from .protobuf import proto_to_sim_data
from .simulation import (
    GameState,
    SimEntity,
    SimTower,
    SimUnit,
    calculate_sim_dt,
)

__all__ = [
    # Game definitions
    "COMBAT_SECONDS",
    "GAME_PATHS",
    "MAP_WIDTH_TILES",
    "PLAYER_LIVES",
    "PREP_SECONDS",
    "START_GOLD",
    "TILE_SIZE_PX",
    "TOWER_STATS",
    "UNIT_STATS",
    "TowerStats",
    "UnitStats",
    "tile_to_pixel",
    # Protocol definitions
    "PlayerID",
    "RoundResultData",
    "RoundStartData",
    "SimTowerData",
    "SimUnitData",
    "SimulationData",
    "GLOBAL_MAP_LAYOUT",
    # Map utilities
    "PlacementGrid",
    # Protobuf utilities
    "proto_to_sim_data",
    # Simulation core
    "GameState",
    "SimEntity",
    "SimTower",
    "SimUnit",
    "calculate_sim_dt",
]
