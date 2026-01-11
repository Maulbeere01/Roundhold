"""Tests for grid definitions and enumerations."""

import pytest

from td_shared.map.grid_defs import GridCellState


class TestGridCellState:
    """Tests for the GridCellState enum."""

    def test_grid_cell_state_values(self):
        """Test that GridCellState has all expected values."""
        assert hasattr(GridCellState, "EMPTY")
        assert hasattr(GridCellState, "BLOCKED")
        assert hasattr(GridCellState, "PATH")
        assert hasattr(GridCellState, "OCCUPIED")

    def test_grid_cell_state_empty(self):
        """Test EMPTY state."""
        state = GridCellState.EMPTY
        assert state == GridCellState.EMPTY

    def test_grid_cell_state_blocked(self):
        """Test BLOCKED state."""
        state = GridCellState.BLOCKED
        assert state == GridCellState.BLOCKED

    def test_grid_cell_state_path(self):
        """Test PATH state."""
        state = GridCellState.PATH
        assert state == GridCellState.PATH

    def test_grid_cell_state_occupied(self):
        """Test OCCUPIED state."""
        state = GridCellState.OCCUPIED
        assert state == GridCellState.OCCUPIED

    def test_grid_cell_state_distinct(self):
        """Test that all states are distinct."""
        states = [
            GridCellState.EMPTY,
            GridCellState.BLOCKED,
            GridCellState.PATH,
            GridCellState.OCCUPIED,
        ]
        
        # All should be different
        assert len(states) == len(set(states))

    def test_grid_cell_state_comparison(self):
        """Test that states can be compared for equality."""
        state1 = GridCellState.EMPTY
        state2 = GridCellState.EMPTY
        state3 = GridCellState.BLOCKED
        
        assert state1 == state2
        assert state1 != state3

    def test_grid_cell_state_in_list(self):
        """Test that states work in lists and conditions."""
        occupied_states = [GridCellState.BLOCKED, GridCellState.PATH, GridCellState.OCCUPIED]
        
        assert GridCellState.BLOCKED in occupied_states
        assert GridCellState.EMPTY not in occupied_states
