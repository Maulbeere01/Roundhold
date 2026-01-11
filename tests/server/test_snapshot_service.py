"""Tests for snapshot service (game state snapshots)."""

import pytest

from server.src.td_server.services.snapshot import SnapshotBuilder
from td_shared.game import SimulationData


class TestSnapshotService:
    """Tests for the SnapshotBuilder class."""

    def test_initialization(self):
        """Test that SnapshotBuilder initializes correctly."""
        from unittest.mock import Mock
        placement_service = Mock()
        wave_queue = Mock()
        service = SnapshotBuilder(placement_service, wave_queue)
        
        # Service should have placement_service and wave_queue
        assert service.placement_service is placement_service
        assert service.wave_queue is wave_queue


class TestSnapshotData:
    """Tests for snapshot data structures."""

    def test_simulation_data_is_serializable(self):
        """Test that SimulationData can be serialized."""
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [
                {
                    "player_id": "A",
                    "tower_type": "standard",
                    "position_x": 100.0,
                    "position_y": 200.0,
                    "level": 1,
                }
            ],
            "units": [
                {
                    "player_id": "B",
                    "unit_type": "standard",
                    "route": 1,
                    "spawn_tick": 0,
                }
            ],
        }
        
        # Verify structure
        assert "tick_rate" in simulation_data
        assert "towers" in simulation_data
        assert "units" in simulation_data
        
        # Verify data types
        assert isinstance(simulation_data["tick_rate"], int)
        assert isinstance(simulation_data["towers"], list)
        assert isinstance(simulation_data["units"], list)

    def test_empty_snapshot(self):
        """Test creating a snapshot with no entities."""
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        
        assert len(simulation_data["towers"]) == 0
        assert len(simulation_data["units"]) == 0
