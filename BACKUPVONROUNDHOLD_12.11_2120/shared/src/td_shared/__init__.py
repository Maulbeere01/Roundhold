"""Shared game definitions and simulation core.

This package contains code that is shared between the server and client,
including game data definitions and deterministic simulation logic.
"""

from .game import (
    GAME_PATHS,
    MAP_WIDTH_TILES,
    TILE_SIZE_PX,
    TOWER_STATS,
    UNIT_STATS,
    TowerStats,
    UnitStats,
    tile_to_pixel,
    PlayerID,
    RoundResultData,
    RoundStartData,
    SimTowerData,
    SimUnitData,
    SimulationData,
)
from .simulation import (
    GameState,
    SimEntity,
    SimTower,
    SimUnit,
    calculate_sim_dt,
)

__all__ = [
    # Game definitions
    "GAME_PATHS",
    "MAP_WIDTH_TILES",
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
    # Simulation core
    "GameState",
    "SimEntity",
    "SimTower",
    "SimUnit",
    "calculate_sim_dt",
]

