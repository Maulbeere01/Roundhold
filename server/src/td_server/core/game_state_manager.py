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
        # Preconditions
        assert initial_lives > 0, f"initial_lives must be > 0, not {initial_lives}"
        assert initial_gold >= 0, f"initial_gold must be >= 0, not {initial_gold}"
        assert (
            default_tick_rate > 0
        ), f"default_tick_rate must be > 0, not {default_tick_rate}"

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

        # Postconditions (invariants)
        assert self.economy is not None, "economy service must not be None"
        assert self.placement is not None, "placement service must not be None"
        assert self.wave_queue is not None, "wave_queue service must not be None"
        assert (
            self.snapshot_builder is not None
        ), "snapshot_builder service must not be None"
        assert (
            self._tick_rate > 0
        ), f"tick_rate must be > 0 after initialization: {self._tick_rate}"
        assert (
            self.economy.get_lives("A") > 0
        ), "Player A lives must be > 0 after initialization"
        assert (
            self.economy.get_lives("B") > 0
        ), "Player B lives must be > 0 after initialization"
        assert (
            self.economy.get_gold("A") >= 0
        ), "Player A gold must be >= 0 after initialization"
        assert (
            self.economy.get_gold("B") >= 0
        ), "Player B gold must be >= 0 after initialization"

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

    def _assert_build_tower_error_postconditions(
        self, player_id: PlayerID, old_gold: int, old_tower_count: int, error_type: str
    ) -> None:
        """Helper method to assert postconditions for build_tower error cases."""
        assert (
            self.economy.get_gold(player_id) == old_gold
        ), f"Gold should be refunded after {error_type} error"
        assert (
            len(self._placed_towers) == old_tower_count
        ), f"No tower should be placed on {error_type} error"

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
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert (
            tower_type in TOWER_STATS
        ), f"tower_type '{tower_type}' does not exist in TOWER_STATS"
        assert level >= 1, f"level must be >= 1, not {level}"
        assert tile_row >= 0, f"tile_row must be >= 0, not {tile_row}"
        assert tile_col >= 0, f"tile_col must be >= 0, not {tile_col}"

        cost = TOWER_STATS[tower_type]["cost"]
        old_gold = self.economy.get_gold(player_id)
        old_tower_count = len(self._placed_towers)

        with self._lock:
            if not self.economy.spend_gold(player_id, cost):
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "spend gold"
                )
                return None

            # 1. Zone Check
            if player_id == "A" and tile_col >= 22:
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "zone check"
                )
                return None
            if player_id == "B" and tile_col < 24:
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "zone check"
                )
                return None

            # 2. Terrain Check (Source of Truth is the Matrix)
            if tile_row < 0 or tile_row >= len(self.map_layout):
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "terrain check"
                )
                return None
            if tile_col < 0 or tile_col >= len(self.map_layout[tile_row]):
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "terrain check"
                )
                return None
            if self.map_layout[tile_row][tile_col] != TILE_TYPE_GRASS:
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "terrain check"
                )
                return None

            # 3. Check if tile is already occupied
            if (tile_row, tile_col) in self._placed_towers:
                self.economy.add_gold(player_id, cost)
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "occupancy check"
                )
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
                self._assert_build_tower_error_postconditions(
                    player_id, old_gold, old_tower_count, "placement"
                )
                return None

            # Track placement
            self._placed_towers[(tile_row, tile_col)] = placed

            # Postcondition for success case
            assert (
                self.economy.get_gold(player_id) == old_gold - cost
            ), f"Gold was not correctly deducted: expected {old_gold - cost}, got {self.economy.get_gold(player_id)}"
            assert (
                (tile_row, tile_col) in self._placed_towers
            ), f"Tower should exist at position ({tile_row}, {tile_col})"
            assert (
                self._placed_towers[(tile_row, tile_col)] == placed
            ), "Placed tower should be correctly stored"
            assert (
                len(self._placed_towers) == old_tower_count + 1
            ), f"Tower count should be increased by 1: expected {old_tower_count + 1}, got {len(self._placed_towers)}"
            assert placed is not None, "Placed tower should not be None"
            assert "player_id" in placed, "Placed tower must have 'player_id' field"
            assert "tower_type" in placed, "Placed tower must have 'tower_type' field"
            assert "position_x" in placed, "Placed tower must have 'position_x' field"
            assert "position_y" in placed, "Placed tower must have 'position_y' field"
            assert "level" in placed, "Placed tower must have 'level' field"
            assert (
                placed["player_id"] == player_id
            ), f"Tower player_id should be {player_id}, not {placed.get('player_id')}"
            assert (
                placed["tower_type"] == tower_type
            ), f"Tower tower_type should be {tower_type}, not {placed.get('tower_type')}"
            assert (
                placed["level"] == level
            ), f"Tower level should be {level}, not {placed.get('level')}"

            return placed

    def add_units_to_wave(self, player_id: PlayerID, units: list[SimUnitData]) -> bool:
        """Append units to the next wave queue with gold validation and deduction."""
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert units is not None, "units must not be None"
        assert len(units) > 0, "units list must not be empty"

        old_gold = self.economy.get_gold(player_id)
        old_queue_size = len(self.wave_queue.get_units())

        with self._lock:
            total_cost, normalized = self.wave_queue.prepare_units(player_id, units)

            if not normalized:
                # Postcondition for error case: gold unchanged, no units added
                assert (
                    self.economy.get_gold(player_id) == old_gold
                ), "Gold should remain unchanged on error"
                assert (
                    len(self.wave_queue.get_units()) == old_queue_size
                ), "No units should be added on error"
                return False

            if not self.economy.spend_gold(player_id, total_cost):
                logger.info(
                    "SendUnits rejected (gold): player=%s, need=%d, have=%d",
                    player_id,
                    total_cost,
                    self.economy.get_gold(player_id),
                )
                # Postcondition for error case: gold unchanged, no units added
                assert (
                    self.economy.get_gold(player_id) == old_gold
                ), "Gold should remain unchanged on error"
                assert (
                    len(self.wave_queue.get_units()) == old_queue_size
                ), "No units should be added on error"
                return False

            self.wave_queue.enqueue_units(normalized, self._tick_rate)
            logger.info(
                "Units queued: player=%s, count=%d, cost=%d",
                player_id,
                len(normalized),
                total_cost,
            )

            # Postcondition for success case
            assert (
                self.economy.get_gold(player_id) == old_gold - total_cost
            ), f"Gold was not correctly deducted: expected {old_gold - total_cost}, got {self.economy.get_gold(player_id)}"
            assert (
                len(self.wave_queue.get_units()) == old_queue_size + len(normalized)
            ), f"Number of units in queue should be increased by {len(normalized)}: expected {old_queue_size + len(normalized)}, got {len(self.wave_queue.get_units())}"
            assert self.economy.get_gold(player_id) >= 0, "Gold must not be negative"

            return True

    def apply_round_result(self, result: RoundResultData) -> None:
        """Apply authoritative round result."""
        with self._lock:
            self.economy.apply_round_result(result)

    def clear_wave_data(self) -> None:
        """Clear queued wave data."""
        with self._lock:
            self.wave_queue.clear()

    def generate_gold_from_mines(self) -> dict[str, int]:
        """Generate gold income from gold mines for both players.

        Returns dict with gold earned per player.
        """
        import random

        generate_mine_gold = lambda count: sum(
            random.randint(5, 15) for _ in range(count)
        )

        with self._lock:
            old_gold_A = self.economy.get_gold("A")
            old_gold_B = self.economy.get_gold("B")

            gold_earned = {
                player_id: generate_mine_gold(
                    self.placement.count_gold_mines(player_id)
                )
                for player_id in ("A", "B")
            }

            # Postcondition: gold_earned must be non-negative
            assert all(
                gold >= 0 for gold in gold_earned.values()
            ), f"Gold earned must be non-negative: {gold_earned}"
            assert "A" in gold_earned, "gold_earned must contain player A"
            assert "B" in gold_earned, "gold_earned must contain player B"

            # Apply gold and log for non-zero earnings
            for player_id, gold in filter(lambda x: x[1] > 0, gold_earned.items()):
                self.economy.add_gold(player_id, gold)
                logger.info(
                    "Player %s earned %d gold from gold mines",
                    player_id,
                    gold,
                )

            # Postconditions
            assert (
                self.economy.get_gold("A") == old_gold_A + gold_earned.get("A", 0)
            ), f"Player A gold not correctly updated: expected {old_gold_A + gold_earned.get('A', 0)}, got {self.economy.get_gold('A')}"
            assert (
                self.economy.get_gold("B") == old_gold_B + gold_earned.get("B", 0)
            ), f"Player B gold not correctly updated: expected {old_gold_B + gold_earned.get('B', 0)}, got {self.economy.get_gold('B')}"
            assert all(
                gold >= 0 for gold in gold_earned.values()
            ), "All gold earned values must be non-negative"

            return gold_earned

    def add_gold_to_players(self, amount: int) -> None:
        """Add gold to both players (e.g., passive income per round).

        Args:
            amount: Gold amount to add to each player.
        """
        # Preconditions
        assert amount >= 0, f"amount must be >= 0, not {amount}"

        with self._lock:
            old_gold_A = self.economy.get_gold("A")
            old_gold_B = self.economy.get_gold("B")

            # Add gold to both players
            self.economy.add_gold("A", amount)
            self.economy.add_gold("B", amount)

            # Postconditions
            assert (
                self.economy.get_gold("A") == old_gold_A + amount
            ), f"Player A gold not correctly updated: expected {old_gold_A + amount}, got {self.economy.get_gold('A')}"
            assert (
                self.economy.get_gold("B") == old_gold_B + amount
            ), f"Player B gold not correctly updated: expected {old_gold_B + amount}, got {self.economy.get_gold('B')}"
