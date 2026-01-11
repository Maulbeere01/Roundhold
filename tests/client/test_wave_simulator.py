"""Tests for WaveSimulator."""

import pytest

from client.src.td_client.simulation.wave_simulator import (
    MAX_ACCUMULATED_TIME,
    WaveSimulator,
)
from td_shared.game import SimulationData


class TestWaveSimulator:
    """Tests for the WaveSimulator class."""

    def test_initialization(self):
        """Test that simulator initializes with no game state."""
        simulator = WaveSimulator()
        assert simulator.game_state is None
        assert simulator._accumulator == 0.0

    def test_load_wave_creates_game_state(self):
        """Test that load_wave creates a new game state."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        
        game_state = simulator.load_wave(simulation_data)
        
        assert game_state is not None
        assert simulator.game_state is game_state
        assert simulator._accumulator == 0.0

    def test_load_wave_resets_accumulator(self):
        """Test that loading a wave resets the accumulator."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        
        simulator._accumulator = 0.5
        simulator.load_wave(simulation_data)
        
        assert simulator._accumulator == 0.0

    def test_update_without_game_state(self):
        """Test that update returns 0 when no game state is loaded."""
        simulator = WaveSimulator()
        ticks = simulator.update(0.016)
        assert ticks == 0

    def test_update_with_zero_dt(self):
        """Test that update returns 0 when dt is zero."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        simulator.load_wave(simulation_data)
        
        ticks = simulator.update(0.0)
        assert ticks == 0

    def test_update_with_negative_dt(self):
        """Test that update returns 0 when dt is negative."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        simulator.load_wave(simulation_data)
        
        ticks = simulator.update(-0.016)
        assert ticks == 0

    def test_update_accumulates_time(self):
        """Test that update accumulates time."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        simulator.load_wave(simulation_data)
        
        # Small dt that won't trigger a tick
        simulator.update(0.01)
        assert simulator._accumulator > 0.0

    def test_update_processes_ticks(self):
        """Test that update processes ticks when enough time accumulated."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,  # 0.05 seconds per tick
            "towers": [],
            "units": [],
        }
        game_state = simulator.load_wave(simulation_data)
        initial_tick = game_state.current_tick
        
        # Accumulate enough for 2 ticks
        ticks = simulator.update(0.1)
        
        assert ticks == 2
        assert game_state.current_tick == initial_tick + 2

    def test_update_leaves_remainder_in_accumulator(self):
        """Test that update leaves remainder time in accumulator."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,  # 0.05 seconds per tick
            "towers": [],
            "units": [],
        }
        simulator.load_wave(simulation_data)
        
        # 0.06 seconds = 1 tick (0.05) + 0.01 remainder
        simulator.update(0.06)
        
        assert 0.009 < simulator._accumulator < 0.011

    def test_update_clamps_accumulator(self):
        """Test that accumulator is clamped to MAX_ACCUMULATED_TIME."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        simulator.load_wave(simulation_data)
        
        # Try to accumulate way too much time
        simulator.update(10.0)
        
        assert simulator._accumulator <= MAX_ACCUMULATED_TIME

    def test_update_stops_when_simulation_complete(self):
        """Test that update stops processing when simulation is complete."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        game_state = simulator.load_wave(simulation_data)
        
        # Advance simulation to completion
        # With no units, min_duration_ticks must pass
        for _ in range(game_state.min_duration_ticks + 100):
            game_state.update_tick()
        
        # Now simulation should be complete
        ticks = simulator.update(0.1)
        assert ticks == 0

    def test_update_multiple_frames(self):
        """Test that multiple update calls work correctly."""
        simulator = WaveSimulator()
        simulation_data: SimulationData = {
            "tick_rate": 20,  # 0.05 seconds per tick
            "towers": [],
            "units": [],
        }
        game_state = simulator.load_wave(simulation_data)
        initial_tick = game_state.current_tick
        
        # Frame 1: 0.03 seconds (not enough for a tick)
        ticks1 = simulator.update(0.03)
        assert ticks1 == 0
        
        # Frame 2: 0.03 seconds (total 0.06, enough for 1 tick)
        ticks2 = simulator.update(0.03)
        assert ticks2 == 1
        
        assert game_state.current_tick == initial_tick + 1

    def test_game_state_property(self):
        """Test that game_state property returns current state."""
        simulator = WaveSimulator()
        assert simulator.game_state is None
        
        simulation_data: SimulationData = {
            "tick_rate": 20,
            "towers": [],
            "units": [],
        }
        game_state = simulator.load_wave(simulation_data)
        
        assert simulator.game_state is game_state
