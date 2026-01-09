from __future__ import annotations

from td_shared.game import SimulationData, tile_to_pixel, MAP_WIDTH_TILES
from td_shared.map.static_map import GLOBAL_MAP_LAYOUT


class SnapshotBuilder:
    """Builds SimulationData snapshots from tower placements and wave queue."""

    def __init__(self, placement_service, wave_queue) -> None:
        self.placement_service = placement_service
        self.wave_queue = wave_queue

    def build(self, tick_rate: int) -> SimulationData:
        towers = self.placement_service.get_sim_towers()

        # Inject castle archer towers for both players at fixed edge positions
        # Rows are based on the center of the global map layout; columns are near edges
        center_row = len(GLOBAL_MAP_LAYOUT) // 2
        left_col = 3
        right_col = MAP_WIDTH_TILES - 4

        left_x, left_y = tile_to_pixel(center_row, left_col)
        right_x, right_y = tile_to_pixel(center_row, right_col)

        # Player A castle archer (left side)
        towers.append({
            "player_id": "A",
            "tower_type": "castle_archer",
            "position_x": float(left_x),
            "position_y": float(left_y),
            "level": 1,
        })

        # Player B castle archer (right side)
        towers.append({
            "player_id": "B",
            "tower_type": "castle_archer",
            "position_x": float(right_x),
            "position_y": float(right_y),
            "level": 1,
        })
        units = self.wave_queue.get_units()
        return SimulationData(
            towers=towers,
            units=units,
            tick_rate=int(tick_rate),
        )

