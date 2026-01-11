"""Tests for WaveQueue service."""

import pytest

from server.src.td_server.services.wave_queue import WaveQueue
from td_shared.game import SimUnitData


class TestWaveQueue:
    """Tests for the WaveQueue class."""

    def test_initialization(self):
        """Test that WaveQueue initializes with empty queue."""
        queue = WaveQueue()
        assert queue._units_next_wave == []

    def test_prepare_units_cost_calculation(self):
        """Test that prepare_units correctly calculates total cost."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "pawn", "route": 1, "spawn_tick": 0},
        ]
        
        total_cost, normalized = queue.prepare_units("A", units)
        
        # standard costs 5, pawn costs 15
        assert total_cost == 5 + 5 + 15

    def test_prepare_units_normalizes_data(self):
        """Test that prepare_units normalizes unit data."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        total_cost, normalized = queue.prepare_units("A", units)
        
        assert len(normalized) == 1
        assert normalized[0]["player_id"] == "A"
        assert normalized[0]["unit_type"] == "standard"
        assert normalized[0]["route"] == 1
        assert normalized[0]["spawn_tick"] == 0

    def test_prepare_units_unknown_type(self):
        """Test that unknown unit types are skipped."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "unknown_unit", "route": 1, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        total_cost, normalized = queue.prepare_units("A", units)
        
        assert len(normalized) == 1  # Only standard unit
        assert total_cost == 5

    def test_enqueue_units_empty_list(self):
        """Test that enqueue_units handles empty list."""
        queue = WaveQueue()
        queue.enqueue_units([], tick_rate=20)
        
        assert len(queue._units_next_wave) == 0

    def test_enqueue_units_assigns_spawn_ticks(self):
        """Test that enqueue_units assigns spawn ticks with delay."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        queue.enqueue_units(units, tick_rate=20)
        
        # delay_ticks = max(1, int(0.5 * 20)) = 10
        assert queue._units_next_wave[0]["spawn_tick"] == 10
        assert queue._units_next_wave[1]["spawn_tick"] == 20

    def test_enqueue_units_multiple_routes(self):
        """Test that spawn ticks are independent per route."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "standard", "route": 2, "spawn_tick": 0},
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        queue.enqueue_units(units, tick_rate=20)
        
        # Both route 1 units should be staggered
        route_1_units = [u for u in queue._units_next_wave if u["route"] == 1]
        route_2_units = [u for u in queue._units_next_wave if u["route"] == 2]
        
        assert route_1_units[0]["spawn_tick"] == 10
        assert route_1_units[1]["spawn_tick"] == 20
        assert route_2_units[0]["spawn_tick"] == 10  # Independent timing

    def test_enqueue_units_respects_existing_spawn_ticks(self):
        """Test that units with existing spawn ticks are not overwritten."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 50},
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        queue.enqueue_units(units, tick_rate=20)
        
        # First unit keeps its spawn tick, second gets assigned
        assert queue._units_next_wave[0]["spawn_tick"] == 50
        assert queue._units_next_wave[1]["spawn_tick"] == 10

    def test_enqueue_units_continues_from_last_spawn(self):
        """Test that new units continue from the last spawn tick."""
        queue = WaveQueue()
        
        # First batch
        units1: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        queue.enqueue_units(units1, tick_rate=20)
        
        # Second batch
        units2: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        queue.enqueue_units(units2, tick_rate=20)
        
        # First unit at tick 10, second at tick 20
        assert queue._units_next_wave[0]["spawn_tick"] == 10
        assert queue._units_next_wave[1]["spawn_tick"] == 20

    def test_clear(self):
        """Test that clear removes all queued units."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
        ]
        
        queue.enqueue_units(units, tick_rate=20)
        assert len(queue._units_next_wave) > 0
        
        queue.clear()
        assert len(queue._units_next_wave) == 0

    def test_get_units(self):
        """Test getting all queued units."""
        queue = WaveQueue()
        units: list[SimUnitData] = [
            {"player_id": "A", "unit_type": "standard", "route": 1, "spawn_tick": 0},
            {"player_id": "B", "unit_type": "pawn", "route": 2, "spawn_tick": 0},
        ]
        
        queue.enqueue_units(units, tick_rate=20)
        
        result = queue._units_next_wave
        assert len(result) == 2
        assert result[0]["unit_type"] == "standard"
        assert result[1]["unit_type"] == "pawn"
