# Event System Summary

## Overview
- Central `EventBus` for publish/subscribe with main-thread dispatch and background-thread queuing.
- Typed, frozen dataclass events for network, client actions, server responses, UI, and state changes.
- Decouples network callbacks, UI interactions, and game state updates via a single bus.

## Key Files
- Core bus: [client/src/td_client/events/event_bus.py](../client/src/td_client/events/event_bus.py)
- Event types: [client/src/td_client/events/events.py](../client/src/td_client/events/events.py)
- App wiring: [client/src/td_client/main.py](../client/src/td_client/main.py), [client/src/td_client/screens/base.py](../client/src/td_client/screens/base.py)
- Network bridge: [client/src/td_client/network/event_router.py](../client/src/td_client/network/event_router.py)
- Screens: [client/src/td_client/screens/game.py](../client/src/td_client/screens/game.py), [client/src/td_client/screens/waiting.py](../client/src/td_client/screens/waiting.py)
- UI actions: [client/src/td_client/ui/build_controller.py](../client/src/td_client/ui/build_controller.py)
- Simulation: [client/src/td_client/simulation/game_simulation.py](../client/src/td_client/simulation/game_simulation.py), [client/src/td_client/simulation/game_factory.py](../client/src/td_client/simulation/game_factory.py)
- Tests: [tests/client/test_event_bus.py](../tests/client/test_event_bus.py)

## What Changed
- **Central bus**: Single EventBus instance owned by `GameApp`; processes pending events each frame.
- **Typed events**: `RoundStartEvent`, `RoundResultEvent`, `TowerPlacedEvent`, `OpponentDisconnectedEvent`, `RequestBuildTowerEvent`, `RequestSendUnitsEvent`, `ToggleBuildModeEvent`, `HoverTileChangedEvent`, etc.
- **Network decoupling**: gRPC callbacks converted to events in `NetworkEventRouter` instead of calling screens directly.
- **Screens**: `GameScreen` listens for round/tower events; `WaitingScreen` listens for queue updates; screens clean up subscriptions on exit.
- **UI flow**: `BuildController` publishes build/send requests and handles responses via events; emits hover/toggle UI events.
- **Simulation**: `GameSimulation` accepts EventBus, keeps compatibility properties, and adds cleanup; factory passes bus through.

## Benefits
- Decoupled communication between network, UI, and simulation layers.
- Thread-safe event handling with queued background events.
- Easier testing and debugging through a single event pipeline.
- Strongly-typed, immutable events reduce coupling and errors.
