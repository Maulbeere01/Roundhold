from __future__ import annotations

from dataclasses import dataclass
from typing import List

from td_shared.game import MAP_WIDTH_TILES, TILE_SIZE_PX, tile_to_pixel, PlayerID, SimTowerData
from td_shared.map import PlacementGrid


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
        grid_A: PlacementGrid,
        grid_B: PlacementGrid,
        *,
        map_width_tiles: int = MAP_WIDTH_TILES,
    ) -> None:
        self.grid_A = grid_A
        self.grid_B = grid_B
        self.map_width_tiles = map_width_tiles
        self._placements: List[TowerPlacement] = []
    
    def get_player_grid(self, player_id: PlayerID) -> PlacementGrid:
        """Get placement grid for a specific player."""
        return self.grid_A if player_id == "A" else self.grid_B

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
        """
        norm_row = int(tile_row)
        norm_col = int(tile_col)

        grid = self.get_player_grid(player_id)


        if not grid.is_buildable(norm_row, norm_col):
            return None

        grid.place_tower(norm_row, norm_col)
        placement = TowerPlacement(
            player_id=player_id,
            tower_type=tower_type,
            tile_row=norm_row,
            tile_col=norm_col,
            level=level,
        )
        self._placements.append(placement)
        return self._placement_to_sim_data(placement)

    def get_sim_towers(self) -> List[SimTowerData]:
        """Return tower placements as SimTowerData list."""
        return [self._placement_to_sim_data(p) for p in self._placements]

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

