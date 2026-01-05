# Event System Summary

## Overview
- Central `EventBus` for publish/subscribe with main-thread dispatch and background-thread queuing.
- Typed, frozen dataclass events for network, client actions, server responses, UI, and state changes.
- Decouples network callbacks, UI interactions, and game state updates via a single bus.

## Key Files
- Core bus: [client/src/td_client/events/event_bus.py](../client/src/td_client/events/event_bus.py)
- Event types: [client/src/td_client/events/events.py](../client/src/td_client/events/events.py)
- App wiring: [client/src/td_client/main.py](../client/src/td_client/main.py), [client/src/td_client/screens/base.py](../client/src/td_client/screens/base.py)
- Network bridge (events→server): [client/src/td_client/network/network_handler.py](../client/src/td_client/network/network_handler.py)
- Network bridge (server→events): [client/src/td_client/network/event_router.py](../client/src/td_client/network/event_router.py)
- Screens: [client/src/td_client/screens/game.py](../client/src/td_client/screens/game.py), [client/src/td_client/screens/waiting.py](../client/src/td_client/screens/waiting.py)
- UI actions: [client/src/td_client/ui/build_controller.py](../client/src/td_client/ui/build_controller.py)
- Simulation: [client/src/td_client/simulation/game_simulation.py](../client/src/td_client/simulation/game_simulation.py), [client/src/td_client/simulation/game_factory.py](../client/src/td_client/simulation/game_factory.py)
- Tests: [tests/client/test_event_bus.py](../tests/client/test_event_bus.py)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EventBus                                    │
│                   (central publish/subscribe)                        │
└────────────┬──────────────────────────────────────┬─────────────────┘
             │                                      │
             ▼                                      ▼
┌────────────────────────┐              ┌────────────────────────────┐
│   NetworkHandler       │              │   NetworkEventRouter       │
│                        │              │                            │
│ Subscribes to:         │              │ gRPC callbacks → Events:   │
│ • RequestBuildTower    │              │ • RoundStartEvent          │
│ • RequestSendUnits     │              │ • RoundResultEvent         │
│ • RequestRoundAck      │              │ • TowerPlacedEvent         │
│                        │              │ • BuildTowerResponseEvent  │
│ Calls NetworkClient ───┼──────────────┼─► Publishes to EventBus    │
└────────────────────────┘              └────────────────────────────┘
             │
             ▼
┌────────────────────────┐
│   NetworkClient        │
│   (gRPC calls)         │
└────────────────────────┘
```

## Event Flow Examples

### Build Tower Flow
1. User clicks tile → `BuildController.handle_mouse_click()`
2. BuildController does optimistic update (deduct gold, place sprite)
3. BuildController publishes `RequestBuildTowerEvent`
4. `NetworkHandler` receives event, calls `network_client.build_tower()`
5. Server responds → `NetworkEventRouter` publishes `BuildTowerResponseEvent`
6. `BuildController._on_build_tower_response()` handles result (rollback if failed)

### Round Ack Flow
1. Simulation completes → `GameSimulation.tick()` detects completion
2. GameSimulation publishes `RequestRoundAckEvent`
3. `NetworkHandler` receives event, calls `network_client.round_ack()`

## What Changed
- **Central bus**: Single EventBus instance owned by `GameApp`; processes pending events each frame.
- **NetworkHandler**: NEW - Bridges action events to NetworkClient calls (no direct network access elsewhere).
- **Typed events**: `RoundStartEvent`, `RoundResultEvent`, `TowerPlacedEvent`, `RequestBuildTowerEvent`, `RequestSendUnitsEvent`, `RequestRoundAckEvent`, `ToggleBuildModeEvent`, `HoverTileChangedEvent`, etc.
- **Network decoupling**: gRPC callbacks converted to events in `NetworkEventRouter`; action requests go through `NetworkHandler`.
- **Screens**: `GameScreen` listens for round/tower events; `WaitingScreen` listens for queue updates; screens clean up subscriptions on exit.
- **UI flow**: `BuildController` publishes build/send requests and handles responses via events; emits hover/toggle UI events.
- **Simulation**: `GameSimulation` publishes `RequestRoundAckEvent` instead of calling NetworkClient directly.

## Benefits
- **Complete decoupling**: No component accesses NetworkClient directly except NetworkHandler.
- **Thread-safe**: Background threads queue events; main thread processes them.
- **Testable**: Mock EventBus to test any component in isolation.
- **Traceable**: All communication flows through a single pipeline.
- **Type-safe**: Frozen dataclass events with clear contracts.
