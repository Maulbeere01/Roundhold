"""Centralized event system for client-side communication."""

from .event_bus import EventBus
from .events import (
    BuildTowerResponseEvent,
    # Client action events (Client -> Server requests)
    ClientActionEvent,
    # Base
    Event,
    GoldChangedEvent,
    HoverTileChangedEvent,
    LivesChangedEvent,
    MatchFoundEvent,
    # Network events (Server -> Client)
    NetworkEvent,
    OpponentDisconnectedEvent,
    PhaseChangedEvent,
    QueueUpdateEvent,
    RequestBuildTowerEvent,
    RequestRoundAckEvent,
    RequestSendUnitsEvent,
    RoundChangedEvent,
    RoundResultEvent,
    RoundStartEvent,
    SendUnitsResponseEvent,
    # Server response events
    ServerResponseEvent,
    # State change events
    StateEvent,
    ToggleBuildModeEvent,
    TowerPlacedEvent,
    # UI/Input events
    UIEvent,
)

__all__ = [
    # Core
    "EventBus",
    "Event",
    # Network events
    "NetworkEvent",
    "MatchFoundEvent",
    "QueueUpdateEvent",
    "RoundStartEvent",
    "RoundResultEvent",
    "TowerPlacedEvent",
    "OpponentDisconnectedEvent",
    # Client action events
    "ClientActionEvent",
    "RequestBuildTowerEvent",
    "RequestSendUnitsEvent",
    "RequestRoundAckEvent",
    # Server response events
    "ServerResponseEvent",
    "BuildTowerResponseEvent",
    "SendUnitsResponseEvent",
    # UI events
    "UIEvent",
    "ToggleBuildModeEvent",
    "HoverTileChangedEvent",
    # State events
    "StateEvent",
    "GoldChangedEvent",
    "LivesChangedEvent",
    "PhaseChangedEvent",
    "RoundChangedEvent",
]
