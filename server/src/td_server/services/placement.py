from __future__ import annotations

from dataclasses import dataclass

from td_shared.game import (
    MAP_WIDTH_TILES,
    TILE_SIZE_PX,
    TOWER_STATS,
    PlayerID,
    SimTowerData,
    tile_to_pixel,
)


@dataclass(frozen=True)
class TowerPlacement:
    player_id: PlayerID
    tower_type: str
    tile_row: int
    tile_col: int
    level: int


class TowerPlacementService:
    """Handles tower placement validation and storage."""

    def __init__(
        self,
        *,
        map_width_tiles: int = MAP_WIDTH_TILES,
    ) -> None:
        self.map_width_tiles = map_width_tiles
        self._placements: list[TowerPlacement] = []

    def place_tower(
        self,
        *,
        player_id: PlayerID,
        tower_type: str,
        tile_row: int,
        tile_col: int,
        level: int,
    ) -> SimTowerData | None:
        """Validate and register a tower placement.

        Returns SimTowerData on success, otherwise None.
        Note: Validation is done in GameStateManager.build_tower().
        This method just creates the placement record.
        """
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

        old_count = len(self._placements)
        norm_row = int(tile_row)
        norm_col = int(tile_col)

        placement = TowerPlacement(
            player_id=player_id,
            tower_type=tower_type,
            tile_row=norm_row,
            tile_col=norm_col,
            level=level,
        )

        self._placements.append(placement)
        result = self._placement_to_sim_data(placement)

        # Postconditions
        assert (
            len(self._placements) == old_count + 1
        ), f"Placement should be added: expected {old_count + 1} placements, got {len(self._placements)}"
        assert (
            self._placements[-1].player_id == player_id
        ), f"Last placement player_id should be {player_id}, not {self._placements[-1].player_id}"
        assert (
            self._placements[-1].tower_type == tower_type
        ), f"Last placement tower_type should be {tower_type}, not {self._placements[-1].tower_type}"
        assert (
            self._placements[-1].tile_row == norm_row
        ), f"Last placement tile_row should be {norm_row}, not {self._placements[-1].tile_row}"
        assert (
            self._placements[-1].tile_col == norm_col
        ), f"Last placement tile_col should be {norm_col}, not {self._placements[-1].tile_col}"
        assert result is not None, "Result should not be None"
        assert (
            result["player_id"] == player_id
        ), f"Result player_id should be {player_id}, not {result.get('player_id')}"
        assert (
            result["tower_type"] == tower_type
        ), f"Result tower_type should be {tower_type}, not {result.get('tower_type')}"

        return result

    def get_sim_towers(self) -> list[SimTowerData]:
        """Return tower placements as SimTowerData list."""
        return [self._placement_to_sim_data(p) for p in self._placements]

    def count_gold_mines(self, player_id: PlayerID) -> int:
        """Count the number of gold mines for a given player."""
        return sum(
            1
            for p in self._placements
            if p.player_id == player_id and p.tower_type == "gold_mine"
        )

    def _placement_to_sim_data(self, placement: TowerPlacement) -> SimTowerData:
        pos_x, pos_y = tile_to_pixel(placement.tile_row, placement.tile_col)
        pos_x += 0.5 * float(TILE_SIZE_PX)
        pos_y += float(TILE_SIZE_PX)

        return SimTowerData(
            player_id=placement.player_id,
            tower_type=placement.tower_type,
            position_x=pos_x,
            position_y=pos_y,
            level=placement.level,
        )
