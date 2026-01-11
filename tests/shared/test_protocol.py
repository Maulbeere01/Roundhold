"""Tests for protocol type definitions and helper functions."""

import pytest

from td_shared.game.protocol import (
    PlayerID,
    RoundResultData,
    SimTowerData,
    SimUnitData,
    SimulationData,
)

# RoundPhase not implemented yet
# from td_shared.game.protocol import RoundPhase


class TestProtocolTypes:
    """Tests for protocol type definitions."""

    def test_player_id_type(self):
        """Test that PlayerID accepts valid values."""
        player_a: PlayerID = "A"
        player_b: PlayerID = "B"
        
        assert player_a == "A"
        assert player_b == "B"


class TestSimTowerData:
    """Tests for SimTowerData TypedDict."""

    def test_sim_tower_data_creation(self):
        """Test creating a valid SimTowerData dict."""
        tower: SimTowerData = {
            "player_id": "A",
            "tower_type": "standard",
            "position_x": 100.0,
            "position_y": 200.0,
            "level": 1,
        }
        
        assert tower["player_id"] == "A"
        assert tower["tower_type"] == "standard"
        assert tower["position_x"] == 100.0
        assert tower["position_y"] == 200.0
        assert tower["level"] == 1

    def test_sim_tower_data_all_types(self):
        """Test creating towers of different types."""
        tower_types = ["standard", "wood_tower", "gold_mine", "castle_archer"]
        
        for tower_type in tower_types:
            tower: SimTowerData = {
                "player_id": "A",
                "tower_type": tower_type,
                "position_x": 0.0,
                "position_y": 0.0,
                "level": 1,
            }
            assert tower["tower_type"] == tower_type


class TestSimUnitData:
    """Tests for SimUnitData TypedDict."""

    def test_sim_unit_data_creation(self):
        """Test creating a valid SimUnitData dict."""
        unit: SimUnitData = {
            "player_id": "A",
            "unit_type": "standard",
            "route": 1,
            "spawn_tick": 0,
        }
        
        assert unit["player_id"] == "A"
        assert unit["unit_type"] == "standard"
        assert unit["route"] == 1
        assert unit["spawn_tick"] == 0

    def test_sim_unit_data_all_types(self):
        """Test creating units of different types."""
        unit_types = ["standard", "pawn", "archer"]
        
        for unit_type in unit_types:
            unit: SimUnitData = {
                "player_id": "B",
                "unit_type": unit_type,
                "route": 2,
                "spawn_tick": 0,
            }
            assert unit["unit_type"] == unit_type

    def test_sim_unit_data_different_routes(self):
        """Test creating units with different routes."""
        for route in [1, 2, 3]:
            unit: SimUnitData = {
                "player_id": "A",
                "unit_type": "standard",
                "route": route,
                "spawn_tick": 0,
            }
            assert unit["route"] == route


class TestSimulationData:
    """Tests for SimulationData TypedDict."""

    def test_simulation_data_creation(self):
        """Test creating a valid SimulationData dict."""
        sim_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        
        assert sim_data["tick_rate"] == 20
        assert sim_data["towers"] == []
        assert sim_data["units"] == []

    def test_simulation_data_with_towers(self):
        """Test SimulationData with tower list."""
        towers: list[SimTowerData] = [
            {
                "player_id": "A",
                "tower_type": "standard",
                "position_x": 100.0,
                "position_y": 200.0,
                "level": 1,
            }
        ]
        
        sim_data: SimulationData = {
            "tick_rate": 20,
            "towers": towers,
            "units": [],
        }
        
        assert len(sim_data["towers"]) == 1
        assert sim_data["towers"][0]["tower_type"] == "standard"

    def test_simulation_data_with_units(self):
        """Test SimulationData with unit list."""
        units: list[SimUnitData] = [
            {
                "player_id": "B",
                "unit_type": "pawn",
                "route": 1,
                "spawn_tick": 0,
            }
        ]
        
        sim_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": units,
        }
        
        assert len(sim_data["units"]) == 1
        assert sim_data["units"][0]["unit_type"] == "pawn"

    def test_simulation_data_with_both(self):
        """Test SimulationData with both towers and units."""
        towers: list[SimTowerData] = [
            {
                "player_id": "A",
                "tower_type": "standard",
                "position_x": 100.0,
                "position_y": 200.0,
                "level": 1,
            }
        ]
        
        units: list[SimUnitData] = [
            {
                "player_id": "B",
                "unit_type": "standard",
                "route": 1,
                "spawn_tick": 0,
            }
        ]
        
        sim_data: SimulationData = {
            "tick_rate": 20,
            "towers": towers,
            "units": units,
        }
        
        assert len(sim_data["towers"]) == 1
        assert len(sim_data["units"]) == 1


class TestRoundResultData:
    """Tests for RoundResultData TypedDict."""

    def test_round_result_data_creation(self):
        """Test creating a valid RoundResultData dict."""
        result: RoundResultData = {
            "lives_lost_player_A": 2,
            "lives_lost_player_B": 3,
            "gold_earned_player_A": 15,
            "gold_earned_player_B": 20,
        }
        
        assert result["lives_lost_player_A"] == 2
        assert result["lives_lost_player_B"] == 3
        assert result["gold_earned_player_A"] == 15
        assert result["gold_earned_player_B"] == 20

    def test_round_result_data_no_damage(self):
        """Test round result with no damage taken."""
        result: RoundResultData = {
            "lives_lost_player_A": 0,
            "lives_lost_player_B": 0,
            "gold_earned_player_A": 10,
            "gold_earned_player_B": 10,
        }
        
        assert result["lives_lost_player_A"] == 0
        assert result["lives_lost_player_B"] == 0

    def test_round_result_data_asymmetric(self):
        """Test round result with asymmetric outcome."""
        result: RoundResultData = {
            "lives_lost_player_A": 0,
            "lives_lost_player_B": 5,
            "gold_earned_player_A": 50,
            "gold_earned_player_B": 5,
        }
        
        # Player A defended well, earned more gold
        assert result["lives_lost_player_A"] < result["lives_lost_player_B"]
        assert result["gold_earned_player_A"] > result["gold_earned_player_B"]
