from __future__ import annotations

from td_shared.game import MAP_WIDTH_TILES, SimulationData, tile_to_pixel
from td_shared.map.static_map import GLOBAL_MAP_LAYOUT


class SnapshotBuilder:
    """Builds SimulationData snapshots from tower placements and wave queue."""

    def __init__(self, placement_service, wave_queue) -> None:
        self.placement_service = placement_service
        self.wave_queue = wave_queue

    def build(self, tick_rate: int) -> SimulationData:
        # Preconditions
        assert tick_rate > 0, f"tick_rate must be > 0, not {tick_rate}"
        assert self.placement_service is not None, "placement_service must not be None"
        assert self.wave_queue is not None, "wave_queue must not be None"

        towers = self.placement_service.get_sim_towers()

        # Inject castle archer towers for both players at fixed edge positions
        # Rows are based on the center of the global map layout; columns are near edges
        center_row = len(GLOBAL_MAP_LAYOUT) // 2
        left_col = 3
        right_col = MAP_WIDTH_TILES - 4

        left_x, left_y = tile_to_pixel(center_row, left_col)
        right_x, right_y = tile_to_pixel(center_row, right_col)

        # Player A castle archer (left side)
        towers.append(
            {
                "player_id": "A",
                "tower_type": "castle_archer",
                "position_x": float(left_x),
                "position_y": float(left_y),
                "level": 1,
            }
        )

        # Player B castle archer (right side)
        towers.append(
            {
                "player_id": "B",
                "tower_type": "castle_archer",
                "position_x": float(right_x),
                "position_y": float(right_y),
                "level": 1,
            }
        )
        units = self.wave_queue.get_units()
        result = SimulationData(
            towers=towers,
            units=units,
            tick_rate=int(tick_rate),
        )

        # Postconditions
        assert isinstance(result, dict), "Result must be a dict"
        assert "towers" in result, "Result must have 'towers' field"
        assert "units" in result, "Result must have 'units' field"
        assert "tick_rate" in result, "Result must have 'tick_rate' field"
        assert (
            result["tick_rate"] == int(tick_rate)
        ), f"tick_rate must match input: expected {tick_rate}, got {result['tick_rate']}"
        assert result["tick_rate"] > 0, f"tick_rate must be > 0: {result['tick_rate']}"
        assert isinstance(result["towers"], list), "towers must be a list"
        assert isinstance(result["units"], list), "units must be a list"
        assert all(
            "player_id" in t for t in result["towers"]
        ), "All towers must have 'player_id' field"
        assert all(
            "tower_type" in t for t in result["towers"]
        ), "All towers must have 'tower_type' field"
        assert all(
            "position_x" in t for t in result["towers"]
        ), "All towers must have 'position_x' field"
        assert all(
            "position_y" in t for t in result["towers"]
        ), "All towers must have 'position_y' field"
        assert all(
            "level" in t for t in result["towers"]
        ), "All towers must have 'level' field"
        assert all(
            t["player_id"] in ("A", "B") for t in result["towers"]
        ), "All tower player_ids must be 'A' or 'B'"
        assert all(
            t["level"] >= 1 for t in result["towers"]
        ), "All tower levels must be >= 1"
        assert all(
            "player_id" in u for u in result["units"]
        ), "All units must have 'player_id' field"
        assert all(
            "unit_type" in u for u in result["units"]
        ), "All units must have 'unit_type' field"
        assert all(
            "route" in u for u in result["units"]
        ), "All units must have 'route' field"
        assert all(
            "spawn_tick" in u for u in result["units"]
        ), "All units must have 'spawn_tick' field"

        return result
