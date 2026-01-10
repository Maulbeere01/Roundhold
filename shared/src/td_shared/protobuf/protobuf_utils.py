"""Protobuf conversion utilities for SimulationData

Centralizes conversion between internal SimulationData (TypedDict) and
gRPC protobuf SimulationData messages. Used by both client and server.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import game_pb2

if TYPE_CHECKING:
    from ..game.protocol import SimulationData


def sim_data_to_proto(sim: SimulationData) -> game_pb2.SimulationData:
    """Convert internal SimulationData dict to protobuf SimulationData

    Args:
        sim: Internal SimulationData TypedDict

    Returns:
        Protobuf SimulationData message
    """
    # Preconditions
    assert isinstance(sim, dict), "sim must be a dict"
    assert (
        sim.get("tick_rate", 0) > 0
    ), f"tick_rate must be > 0, not {sim.get('tick_rate')}"

    towers = []
    for t in sim["towers"]:
        assert t.get("player_id") in (
            "A",
            "B",
        ), f"Tower player_id must be 'A' or 'B', not '{t.get('player_id')}'"
        towers.append(
            game_pb2.SimTowerData(
                player_id=t["player_id"],
                tower_type=t["tower_type"],
                position_x=float(t["position_x"]),
                position_y=float(t["position_y"]),
                level=int(t["level"]),
            )
        )

    units = []
    for u in sim["units"]:
        assert u.get("player_id") in (
            "A",
            "B",
        ), f"Unit player_id must be 'A' or 'B', not '{u.get('player_id')}'"
        units.append(
            game_pb2.SimUnitData(
                player_id=u["player_id"],
                unit_type=u["unit_type"],
                route=int(u["route"]),
                spawn_tick=int(u["spawn_tick"]),
            )
        )

    result = game_pb2.SimulationData(
        towers=towers,
        units=units,
        tick_rate=int(sim["tick_rate"]),
    )

    # Postcondition
    assert len(result.towers) == len(sim["towers"]), "Tower count must match input"
    assert len(result.units) == len(sim["units"]), "Unit count must match input"

    return result


def proto_to_sim_data(sim_proto: game_pb2.SimulationData) -> SimulationData:
    """Convert protobuf SimulationData to internal SimulationData dict.

    Args:
        sim_proto: Protobuf SimulationData message

    Returns:
        Internal SimulationData TypedDict
    """
    # Preconditions
    assert sim_proto is not None, "sim_proto must not be None"
    assert sim_proto.tick_rate > 0, f"tick_rate must be > 0, not {sim_proto.tick_rate}"

    from ..game.protocol import SimulationData

    towers = []
    for t in sim_proto.towers:
        assert t.player_id in (
            "A",
            "B",
        ), f"Tower player_id must be 'A' or 'B', not '{t.player_id}'"
        towers.append(
            {
                "player_id": t.player_id,
                "tower_type": t.tower_type,
                "position_x": float(t.position_x),
                "position_y": float(t.position_y),
                "level": int(t.level),
            }
        )

    units = []
    for u in sim_proto.units:
        assert u.player_id in (
            "A",
            "B",
        ), f"Unit player_id must be 'A' or 'B', not '{u.player_id}'"
        units.append(
            {
                "player_id": u.player_id,
                "unit_type": u.unit_type,
                "route": int(u.route),
                "spawn_tick": int(u.spawn_tick),
            }
        )

    result = SimulationData(
        towers=towers,
        units=units,
        tick_rate=int(sim_proto.tick_rate),
    )

    # Postconditions
    assert len(result["towers"]) == len(
        sim_proto.towers
    ), "Tower count must match input"
    assert len(result["units"]) == len(sim_proto.units), "Unit count must match input"

    return result
