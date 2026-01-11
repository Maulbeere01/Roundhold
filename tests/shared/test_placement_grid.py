"""Tests for PlacementGrid class."""

import pytest

from td_shared.map.grid_defs import GridCellState
from td_shared.map.placement_grid import PlacementGrid
from td_shared.map.static_map import TILE_TYPE_GRASS, TILE_TYPE_PATH


class TestPlacementGrid:
    """Tests for the PlacementGrid class."""

    def test_initialization(self):
        """Test that grid is properly initialized from layout."""
        layout = [
            [TILE_TYPE_GRASS, TILE_TYPE_GRASS, TILE_TYPE_PATH],
            [TILE_TYPE_GRASS, TILE_TYPE_GRASS, TILE_TYPE_GRASS],
        ]
        grid = PlacementGrid(layout)
        
        assert grid.height_tiles == 2
        assert grid.width_tiles == 3
        assert grid.grid[0][0] == GridCellState.EMPTY  # Grass
        assert grid.grid[0][1] == GridCellState.EMPTY  # Grass
        assert grid.grid[0][2] == GridCellState.PATH   # Path
        assert grid.grid[1][0] == GridCellState.EMPTY  # Grass

    def test_is_buildable_on_grass(self):
        """Test that grass tiles are buildable."""
        layout = [[TILE_TYPE_GRASS, TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        assert grid.is_buildable(0, 0) is True
        assert grid.is_buildable(0, 1) is True

    def test_is_buildable_on_path(self):
        """Test that path tiles are not buildable."""
        layout = [[TILE_TYPE_PATH]]
        grid = PlacementGrid(layout)
        
        assert grid.is_buildable(0, 0) is False

    def test_is_buildable_out_of_bounds(self):
        """Test that out-of-bounds coordinates are not buildable."""
        layout = [[TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        assert grid.is_buildable(-1, 0) is False
        assert grid.is_buildable(0, -1) is False
        assert grid.is_buildable(1, 0) is False
        assert grid.is_buildable(0, 1) is False

    def test_validate_build_player_a_in_zone(self):
        """Test that Player A can build in their zone (left side)."""
        layout = [[TILE_TYPE_GRASS] * 10]
        grid = PlacementGrid(layout)
        
        # Player A should be able to build on left side (col <= ZONE_BOUNDARY_LEFT)
        # ZONE_BOUNDARY_LEFT is typically around 16-18
        assert grid.validate_build("A", 0, 0) is True
        assert grid.validate_build("A", 0, 5) is True

    def test_validate_build_player_b_in_zone(self):
        """Test that Player B can build in their zone (right side)."""
        layout = [[TILE_TYPE_GRASS] * 40]
        grid = PlacementGrid(layout)
        
        # Player B should be able to build on right side (col >= ZONE_BOUNDARY_RIGHT)
        # ZONE_BOUNDARY_RIGHT is typically around 21-23
        assert grid.validate_build("B", 0, 30) is True
        assert grid.validate_build("B", 0, 39) is True

    def test_validate_build_outside_zone(self):
        """Test that players cannot build outside their zones."""
        layout = [[TILE_TYPE_GRASS] * 40]
        grid = PlacementGrid(layout)
        
        # Player A should not be able to build on right side
        assert grid.validate_build("A", 0, 35) is False
        
        # Player B should not be able to build on left side
        assert grid.validate_build("B", 0, 5) is False

    def test_place_tower_success(self):
        """Test successful tower placement."""
        layout = [[TILE_TYPE_GRASS, TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        result = grid.place_tower(0, 0)
        assert result is True
        assert grid.grid[0][0] == GridCellState.OCCUPIED

    def test_place_tower_on_occupied(self):
        """Test that tower cannot be placed on occupied tile."""
        layout = [[TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        grid.place_tower(0, 0)
        result = grid.place_tower(0, 0)  # Try to place again
        assert result is False

    def test_place_tower_on_path(self):
        """Test that tower cannot be placed on path."""
        layout = [[TILE_TYPE_PATH]]
        grid = PlacementGrid(layout)
        
        result = grid.place_tower(0, 0)
        assert result is False

    def test_clear_tower(self):
        """Test clearing a tower from a tile."""
        layout = [[TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        grid.place_tower(0, 0)
        assert grid.grid[0][0] == GridCellState.OCCUPIED
        
        grid.clear_tower(0, 0)
        assert grid.grid[0][0] == GridCellState.EMPTY

    def test_clear_tower_on_empty(self):
        """Test clearing tower on empty tile (should do nothing)."""
        layout = [[TILE_TYPE_GRASS]]
        grid = PlacementGrid(layout)
        
        grid.clear_tower(0, 0)  # Should not raise error
        assert grid.grid[0][0] == GridCellState.EMPTY
