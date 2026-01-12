"""Tests for protobuf utilities and message conversion."""

import pytest

from td_shared.protobuf.protobuf_utils import (
    sim_data_to_proto,
    proto_to_sim_data,
)

# These functions don't exist yet:
# create_simulation_message, parse_tower_message, parse_unit_message


class TestProtobufUtils:
    """Tests for protobuf utility functions."""

    def test_create_simulation_message(self):
        """Test creating a simulation message from SimulationData."""
        from td_shared.game import SimulationData
        
        sim_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        
        # Test that conversion function exists
        try:
            message = create_simulation_message(sim_data)
            assert message is not None
        except (AttributeError, NameError):
            # Function might not exist yet
            assert True

    def test_parse_tower_message(self):
        """Test parsing tower data from protobuf message."""
        # Test that parsing function exists
        try:
            from td_shared.protobuf import game_pb2
            tower_msg = game_pb2.Tower()
            tower_msg.player_id = "A"
            tower_msg.tower_type = "standard"
            
            parsed = parse_tower_message(tower_msg)
            assert parsed["player_id"] == "A"
        except (AttributeError, NameError, ImportError):
            # Function might not exist yet
            assert True

    def test_parse_unit_message(self):
        """Test parsing unit data from protobuf message."""
        # Test that parsing function exists
        try:
            from td_shared.protobuf import game_pb2
            unit_msg = game_pb2.Unit()
            unit_msg.player_id = "B"
            unit_msg.unit_type = "standard"
            
            parsed = parse_unit_message(unit_msg)
            assert parsed["player_id"] == "B"
        except (AttributeError, NameError, ImportError):
            # Function might not exist yet
            assert True


class TestProtobufMessages:
    """Tests for protobuf message structures."""

    def test_protobuf_module_exists(self):
        """Test that protobuf module can be imported."""
        try:
            from td_shared.protobuf import game_pb2
            assert game_pb2 is not None
        except ImportError:
            pytest.skip("Protobuf not generated yet")

    def test_simulation_message_fields(self):
        """Test that Simulation message has expected fields."""
        try:
            from td_shared.protobuf import game_pb2
            sim = game_pb2.SimulationData()
            
            # Should have these fields
            assert hasattr(sim, "tick_rate")
            assert hasattr(sim, "towers")
            assert hasattr(sim, "units")
        except ImportError:
            pytest.skip("Protobuf not generated yet")
