"""Protocol definitions for client-server communication.

This module defines the data structures (TypedDict) that represent the messages
exchanged between server and client during the game phases. These structures
serve as contracts for the deterministic lockstep simulation.

These TypedDicts mirror the data structures used by our gRPC protobuf definitions
and act as type-safe Python contracts for server and client code.
"""
from typing import List, Literal, TypedDict


PlayerID = Literal["A", "B"]


class SimTowerData(TypedDict):
    """Tower data for simulation start.
    
    Represents a single tower that exists at the start of a round.
    Both players' towers are included in the simulation data.
    
    Attributes:
        player_id: Player who owns this tower ("A" or "B")
        tower_type: Type identifier (e.g., "standard")
        position_x: X coordinate in pixels
        position_y: Y coordinate in pixels
        level: Tower level (1 = base level, higher = upgraded)
    """
    player_id: PlayerID
    tower_type: str
    position_x: float
    position_y: float
    level: int


class SimUnitData(TypedDict):
    """Unit data for simulation start.
    
    Represents a single unit that will spawn during the round.
    Both players' units are included in the simulation data.
    
    Attributes:
        player_id: Player who owns this unit ("A" or "B")
        unit_type: Type identifier (e.g., "standard")
        route: Route number (1-5) that this unit will follow
        spawn_tick: Simulation tick at which this unit spawns (0-based)
    """
    player_id: PlayerID
    unit_type: str
    route: int
    spawn_tick: int


class SimulationData(TypedDict):
    """Complete simulation data for a round.
    
    Contains all data needed to run a deterministic simulation.
    This structure is sent from server to client in Phase 2 (RoundStart).
    
    Attributes:
        towers: List of all towers (both players) at round start
        units: List of all units (both players) that will spawn during the round
        tick_rate: Simulation tick rate (e.g., 20 ticks per second)
    """
    towers: List[SimTowerData]
    units: List[SimUnitData]
    tick_rate: int


class RoundStartData(TypedDict):
    """Round start message data.
    
    Sent from server to client in Phase 2 to initiate the simulation.
    
    Attributes:
        simulation_data: Complete simulation data for the round
    """
    simulation_data: SimulationData


class RoundResultData(TypedDict):
    """Round result message data.
    
    Sent from server to client after simulation completes.
    Contains the authoritative results that override any client-side calculations
    
    Attributes:
        lives_lost_player_A: Number of lives lost by player A
        gold_earned_player_A: Gold earned by player A this round
        lives_lost_player_B: Number of lives lost by player B
        gold_earned_player_B: Gold earned by player B this round
    """
    lives_lost_player_A: int
    gold_earned_player_A: int
    lives_lost_player_B: int
    gold_earned_player_B: int

