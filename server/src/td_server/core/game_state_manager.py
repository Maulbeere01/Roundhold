from __future__ import annotations

import logging
import threading

from td_shared.game import (
    DEFAULT_TICK_RATE,
    MAP_WIDTH_TILES,
    PLAYER_LIVES,
    START_GOLD,
    TOWER_STATS,
    PlayerID,
    RoundResultData,
    SimTowerData,
    SimulationData,
    SimUnitData,
)
from td_shared.map.static_map import GLOBAL_MAP_LAYOUT, TILE_TYPE_GRASS

from ..services import EconomyManager, SnapshotBuilder, TowerPlacementService, WaveQueue

logger = logging.getLogger(__name__)


class GameStateManager:
    """Authoritative state container with lock-guarded mutations."""

    def __init__(
        self,
        *,
        initial_lives: int = PLAYER_LIVES,
        initial_gold: int = START_GOLD,
        default_tick_rate: int = DEFAULT_TICK_RATE,
        economy: EconomyManager | None = None,
        placement: TowerPlacementService | None = None,
        wave_queue: WaveQueue | None = None,
        snapshot_builder: SnapshotBuilder | None = None,
    ) -> None:
        # Static global map layout
        self.map_layout = GLOBAL_MAP_LAYOUT

        # Track placed towers (row, col) -> TowerPlacement
        self._placed_towers: dict[tuple[int, int], SimTowerData] = {}

        # Services
        self.economy = economy or EconomyManager(initial_lives, initial_gold)
        self.placement = placement or TowerPlacementService(
            map_width_tiles=MAP_WIDTH_TILES
        )

        self.wave_queue = wave_queue or WaveQueue()
        self.snapshot_builder = snapshot_builder or SnapshotBuilder(
            self.placement, self.wave_queue
        )

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
    ) -> SimTowerData | None:
        """Spend gold and place a tower atomically."""
        if level < 1:
            raise ValueError("level must be >= 1")
        if tower_type not in TOWER_STATS:
            raise ValueError(f"Unknown tower_type: {tower_type}")

        cost = TOWER_STATS[tower_type]["cost"]
        with self._lock:
            if not self.economy.spend_gold(player_id, cost):
                return None

            # 1. Zone Check
            if player_id == "A" and tile_col >= 22:
                self.economy.add_gold(player_id, cost)
                return None
            if player_id == "B" and tile_col < 24:
                self.economy.add_gold(player_id, cost)
                return None

            # 2. Terrain Check (Source of Truth is the Matrix)
            if tile_row < 0 or tile_row >= len(self.map_layout):
                self.economy.add_gold(player_id, cost)
                return None
            if tile_col < 0 or tile_col >= len(self.map_layout[tile_row]):
                self.economy.add_gold(player_id, cost)
                return None
            if self.map_layout[tile_row][tile_col] != TILE_TYPE_GRASS:
                self.economy.add_gold(player_id, cost)
                return None

            # 3. Check if tile is already occupied
            if (tile_row, tile_col) in self._placed_towers:
                self.economy.add_gold(player_id, cost)
                return None

            # 4. Place tower
            placed = self.placement.place_tower(
                player_id=player_id,
                tower_type=tower_type,
                tile_row=tile_row,
                tile_col=tile_col,
                level=level,
            )

            if placed is None:
                # Refund on failure
                self.economy.add_gold(player_id, cost)
                return None

            # Track placement
            self._placed_towers[(tile_row, tile_col)] = placed
            return placed

    def add_units_to_wave(self, player_id: PlayerID, units: list[SimUnitData]) -> bool:
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
            logger.info(
                "Units queued: player=%s, count=%d, cost=%d",
                player_id,
                len(normalized),
                total_cost,
            )
            return True

    def apply_round_result(self, result: RoundResultData) -> None:
        """Apply authoritative round result."""
        with self._lock:
            self.economy.apply_round_result(result)

    def clear_wave_data(self) -> None:
        """Clear queued wave data."""
        with self._lock:
            self.wave_queue.clear()
