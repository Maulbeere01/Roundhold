"""Protobuf conversion utilities for SimulationData

Centralizes conversion between internal SimulationData (TypedDict) and
gRPC protobuf SimulationData messages. Used by both client and server.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from . import game_pb2

if TYPE_CHECKING:
    from ..game.protocol import SimulationData


def sim_data_to_proto(sim: "SimulationData") -> "game_pb2.SimulationData":
    """Convert internal SimulationData dict to protobuf SimulationData
    
    Args:
        sim: Internal SimulationData TypedDict
        
    Returns:
        Protobuf SimulationData message
    """
    
    towers = []
    for t in sim["towers"]:
        towers.append(game_pb2.SimTowerData(
            player_id=t["player_id"],
            tower_type=t["tower_type"],
            position_x=float(t["position_x"]),
            position_y=float(t["position_y"]),
            level=int(t["level"]),
        ))
    
    units = []
    for u in sim["units"]:
        units.append(game_pb2.SimUnitData(
            player_id=u["player_id"],
            unit_type=u["unit_type"],
            route=int(u["route"]),
            spawn_tick=int(u["spawn_tick"]),
        ))
    
    return game_pb2.SimulationData(
        towers=towers,
        units=units,
        tick_rate=int(sim["tick_rate"]),
    )


def proto_to_sim_data(sim_proto: "game_pb2.SimulationData") -> "SimulationData":
    """Convert protobuf SimulationData to internal SimulationData dict.
    
    Args:
        sim_proto: Protobuf SimulationData message
        
    Returns:
        Internal SimulationData TypedDict
    """
    from ..game.protocol import SimulationData
    
    return SimulationData(
        towers=[
            {
                "player_id": t.player_id,
                "tower_type": t.tower_type,
                "position_x": float(t.position_x),
                "position_y": float(t.position_y),
                "level": int(t.level),
            }
            for t in sim_proto.towers
        ],
        units=[
            {
                "player_id": u.player_id, 
                "unit_type": u.unit_type,
                "route": int(u.route),
                "spawn_tick": int(u.spawn_tick),
            }
            for u in sim_proto.units
        ],
        tick_rate=int(sim_proto.tick_rate),
    )

