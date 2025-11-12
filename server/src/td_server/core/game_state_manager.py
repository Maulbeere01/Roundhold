from __future__ import annotations

import logging
import threading
from typing import List, Optional
from td_shared.map import PlacementGrid, mirror_paths_for_width, infer_height_from_paths
from ..services import EconomyManager, TowerPlacementService, WaveQueue, SnapshotBuilder
from td_shared.game import (
    TOWER_STATS,
    MAP_WIDTH_TILES,
    GAME_PATHS,
    PLAYER_LIVES,
    START_GOLD,
    DEFAULT_TICK_RATE,
    PlayerID,
    SimTowerData,
    SimUnitData,
    SimulationData,
    RoundResultData,
)


logger = logging.getLogger(__name__)


class GameStateManager:
    """Authoritative state container with lock-guarded mutations."""

    def __init__(
        self,
        *,
        initial_lives: int = PLAYER_LIVES,
        initial_gold: int = START_GOLD,
        default_tick_rate: int = DEFAULT_TICK_RATE,
        economy: Optional[EconomyManager] = None,
        placement: Optional[TowerPlacementService] = None,
        wave_queue: Optional[WaveQueue] = None,
        snapshot_builder: Optional[SnapshotBuilder] = None,
    ) -> None:
        # Shared placement grids for each player side
        height_tiles = infer_height_from_paths(GAME_PATHS)
        self.grid_A = PlacementGrid(MAP_WIDTH_TILES, height_tiles)
        self.grid_B = PlacementGrid(MAP_WIDTH_TILES, height_tiles)
        self.grid_A.populate_from_paths(GAME_PATHS)
        self.grid_B.populate_from_paths(mirror_paths_for_width(GAME_PATHS, MAP_WIDTH_TILES))

        # Services
        self.economy = economy or EconomyManager(initial_lives, initial_gold)
        self.placement = placement or TowerPlacementService(self.grid_A, self.grid_B, map_width_tiles=MAP_WIDTH_TILES)
        self.wave_queue = wave_queue or WaveQueue()
        self.snapshot_builder = snapshot_builder or SnapshotBuilder(self.placement, self.wave_queue)

        # Simulation config
        self._tick_rate: int = default_tick_rate

        # Concurrency primitive
        self._lock = threading.Lock()

    # Player-specific access methods
    def get_player_gold(self, player_id: PlayerID) -> int:
        """Get gold for a specific player."""
        return self.economy.get_gold(player_id)

    def get_player_lives(self, player_id: PlayerID) -> int:
        """Get lives for a specific player."""
        return self.economy.get_lives(player_id)

    # Backwards-compatible properties for gold/lives access
    @property
    def player_A_gold(self) -> int:
        return self.economy.get_gold("A")

    @property
    def player_B_gold(self) -> int:
        return self.economy.get_gold("B")

    @property
    def player_A_lives(self) -> int:
        return self.economy.get_lives("A")

    @property
    def player_B_lives(self) -> int:
        return self.economy.get_lives("B")

    @property
    def tick_rate(self) -> int:
        return self._tick_rate

    def set_tick_rate(self, tick_rate: int) -> None:
        if tick_rate <= 0:
            raise ValueError("tick_rate must be > 0")
        self._tick_rate = tick_rate

    def get_current_state_snapshot(self) -> SimulationData:
        """Return SimulationData snapshot for the next round."""
        with self._lock:
            return self.snapshot_builder.build(self._tick_rate)

    def build_tower(
        self,
        *,
        player_id: PlayerID,
        tower_type: str,
        tile_row: int,
        tile_col: int,
        level: int = 1,
    ) -> Optional[SimTowerData]:
        """Spend gold and place a tower atomically."""
        if level < 1:
            raise ValueError("level must be >= 1")
        if tower_type not in TOWER_STATS:
            raise ValueError(f"Unknown tower_type: {tower_type}")

        cost = TOWER_STATS[tower_type]["cost"]
        with self._lock:
            if not self.economy.spend_gold(player_id, cost):
                return None

            placed = self.placement.place_tower(
                player_id=player_id,
                tower_type=tower_type,
                tile_row=tile_row,
                tile_col=tile_col,
                level=level,
            )

            if placed is None:
                # Refund on failure (e.g. invalid placement)
                self.economy.add_gold(player_id, cost)
                return None
            return placed

    def add_units_to_wave(self, player_id: PlayerID, units: List[SimUnitData]) -> bool:
        """Append units to the next wave queue with gold validation and deduction."""
        with self._lock:
            total_cost, normalized = self.wave_queue.prepare_units(player_id, units)
            if not normalized:
                return False

            if not self.economy.spend_gold(player_id, total_cost):
                logger.info(
                    "SendUnits rejected (gold): player=%s, need=%d, have=%d",
                    player_id,
                    total_cost,
                    self.economy.get_gold(player_id),
                )
                return False

            self.wave_queue.enqueue_units(normalized, self._tick_rate)
            logger.info("Units queued: player=%s, count=%d, cost=%d", player_id, len(normalized), total_cost)
            return True

    def apply_round_result(self, result: RoundResultData) -> None:
        """Apply authoritative round result."""
        with self._lock:
            self.economy.apply_round_result(result)

    def clear_wave_data(self) -> None:
        """Clear queued wave data."""
        with self._lock:
            self.wave_queue.clear()
