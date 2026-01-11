# Test Suite for Roundhold Tower Defense Game

This directory contains comprehensive unit tests for the Roundhold project.

## Test Structure

### Client Tests (`tests/client/`)
- `test_event_bus.py` - Event system and pub/sub mechanism
- `test_wave_simulator.py` - Wave simulation timing and updates
- `test_event_router.py` - Network event routing
- `test_game_states.py` - Game state management
- `test_game_factory.py` - Game object creation patterns
- `test_input_controller.py` - User input handling

### Server Tests (`tests/server/`)
- `test_combat_simulation.py` - Combat simulation logic
- `test_economy_manager.py` - Economy and gold management
- `test_game_state_manager.py` - Server-side game state
- `test_wave_queue.py` - Unit queuing and spawn timing
- `test_placement_service.py` - Tower placement validation
- `test_economy_service.py` - Economy service logic
- `test_snapshot_service.py` - Game state snapshots
- `test_round_manager.py` - Round management and phases

### Shared Tests (`tests/shared/`)
- `test_placement_grid.py` - Grid placement and validation
- `test_game_balance.py` - Game balance constants and calculations
- `test_entities.py` - Simulation entity classes (units, towers)
- `test_protocol.py` - Protocol types and data structures
- `test_grid_defs.py` - Grid state enumerations
- `test_static_map.py` - Static map layout and definitions
- `test_protobuf_utils.py` - Protobuf message utilities

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run specific test file:
```bash
pytest tests/client/test_event_bus.py
```

### Run with coverage:
```bash
pytest --cov=client --cov=server --cov=shared tests/
```

### Run tests for a specific module:
```bash
pytest tests/server/  # All server tests
pytest tests/client/  # All client tests
pytest tests/shared/  # All shared tests
```

### Run with verbose output:
```bash
pytest -v tests/
```

## Test Coverage

The test suite covers:

1. **Core Game Logic**
   - Unit and tower simulation
   - Combat mechanics
   - Path following
   - Damage calculation

2. **Map and Placement**
   - Grid validation
   - Zone restrictions
   - Buildable tile detection
   - Coordinate conversions

3. **Economy System**
   - Gold management
   - Tower costs
   - Unit costs
   - Kill rewards
   - Gold mine income

4. **Event System**
   - Event publishing
   - Event subscription
   - Event routing
   - Network events

5. **Game State Management**
   - Round phases
   - State transitions
   - Simulation timing
   - State snapshots

6. **Data Structures**
   - Protocol types
   - Simulation data
   - Tower/unit data
   - Round results

## Test Guidelines

- Tests are organized by component (client/server/shared)
- Each test class focuses on a single module/class
- Test methods should be descriptive and test one behavior
- Use pytest fixtures for common setup
- Mock external dependencies when needed
- Tests should be fast and independent

## Dependencies

Tests require:
- pytest
- pygame (for client tests)
- All project dependencies from requirements-dev.txt
