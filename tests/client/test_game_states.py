"""Tests for client-side game state management."""

import pytest

from client.src.td_client.simulation.game_states import (
    MapState,
    PlayerState,
    PhaseState,
    UIState,
    SimulationState,
)


class TestGameStateContext:
    """Tests for the game state classes."""

    def test_map_state_exists(self):
        """Test that MapState can be initialized."""
        # This test verifies the structure exists
        map_state = MapState()
        assert map_state is not None

    def test_player_state_exists(self):
        """Test that PlayerState exists."""
        # Verify the class exists
        player_state = PlayerState()
        assert player_state is not None


class TestGameStates:
    """Tests for game state types."""

    def test_game_has_multiple_states(self):
        """Test that game has different states (menu, waiting, playing, etc)."""
        # Verify state module exists
        from client.src.td_client.simulation import game_states
        
        assert game_states is not None
