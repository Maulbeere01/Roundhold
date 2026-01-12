"""Tests for simulation entity classes."""

import pytest

from td_shared.game import SimulationData
from td_shared.simulation import GameState, SimUnit


class TestSimUnit:
    """Tests for the SimUnit class."""

    def test_unit_initialization(self):
        """Test that unit initializes with correct stats."""
        unit = SimUnit(
            entity_id=1,
            player_id="A",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        assert unit.entity_id == 1
        assert unit.player_id == "A"
        assert unit.unit_type == "standard"
        assert unit.route == 1
        assert unit.health == unit.max_health
        assert unit.health == 50  # Standard unit has 50 HP
        assert unit.is_active is True

    def test_unit_initialization_invalid_type(self):
        """Test that invalid unit type raises error."""
        with pytest.raises(ValueError, match="Unknown unit type"):
            SimUnit(
                entity_id=1,
                player_id="A",
                unit_type="invalid_unit",
                route=1,
                sim_dt=0.05,
            )

    def test_unit_initialization_invalid_player(self):
        """Test that invalid player ID raises error."""
        with pytest.raises(AssertionError, match="player_id must be"):
            SimUnit(
                entity_id=1,
                player_id="X",  # Invalid player
                unit_type="standard",
                route=1,
                sim_dt=0.05,
            )

    def test_unit_initialization_invalid_route(self):
        """Test that invalid route raises error."""
        with pytest.raises(ValueError, match="Unknown route"):
            SimUnit(
                entity_id=1,
                player_id="A",
                unit_type="standard",
                route=999,  # Invalid route
                sim_dt=0.05,
            )

    def test_unit_has_path(self):
        """Test that unit has a valid path."""
        unit = SimUnit(
            entity_id=1,
            player_id="A",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        assert len(unit.path) > 0
        assert unit.current_path_index == 0

    def test_unit_take_damage(self):
        """Test that unit takes damage correctly."""
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        game_state = GameState(simulation_data)
        
        unit = SimUnit(
            entity_id=1,
            player_id="B",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        initial_health = unit.health
        unit.take_damage(10, "A", game_state)
        
        assert unit.health == initial_health - 10
        assert unit.is_active is True

    def test_unit_dies_from_damage(self):
        """Test that unit dies when health reaches zero."""
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        game_state = GameState(simulation_data)
        
        unit = SimUnit(
            entity_id=1,
            player_id="B",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        unit.take_damage(100, "A", game_state)
        
        assert unit.health == 0
        assert unit.is_active is False

    def test_unit_death_increments_kill_count(self):
        """Test that unit death increments attacker's kill count."""
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        game_state = GameState(simulation_data)
        
        unit = SimUnit(
            entity_id=1,
            player_id="B",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        initial_gold = game_state.gold_earned_by_player_A
        unit.take_damage(100, "A", game_state)
        
        assert game_state.gold_earned_by_player_A > initial_gold

    def test_unit_different_types_different_stats(self):
        """Test that different unit types have different stats."""
        standard = SimUnit(
            entity_id=1,
            player_id="A",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        pawn = SimUnit(
            entity_id=2,
            player_id="A",
            unit_type="pawn",
            route=1,
            sim_dt=0.05,
        )
        
        archer = SimUnit(
            entity_id=3,
            player_id="A",
            unit_type="archer",
            route=1,
            sim_dt=0.05,
        )
        
        # Pawn has more health
        assert pawn.max_health > standard.max_health
        
        # Archer has less health but higher damage
        assert archer.max_health < standard.max_health
        assert archer.base_damage > standard.base_damage

    def test_unit_spawn_offset(self):
        """Test that unit has spawn offset attributes."""
        unit = SimUnit(
            entity_id=1,
            player_id="A",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        assert hasattr(unit, "spawn_offset_x")
        assert hasattr(unit, "spawn_offset_y")
        assert hasattr(unit, "ease_progress")
        assert unit.ease_progress == 1.0  # Fully on path initially

    def test_unit_reached_base_flag(self):
        """Test that unit has reached_base flag."""
        unit = SimUnit(
            entity_id=1,
            player_id="A",
            unit_type="standard",
            route=1,
            sim_dt=0.05,
        )
        
        assert hasattr(unit, "_reached_base")
        assert unit._reached_base is False
