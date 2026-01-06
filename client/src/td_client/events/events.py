from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from td_shared import PlayerID

# =============================================================================
# Base Event Classes
# =============================================================================


@dataclass(frozen=True)
class Event:
    """Base class for all events."""

    pass


# =============================================================================
# Network Events (Server -> Client via gRPC stream)
# =============================================================================


@dataclass(frozen=True)
class NetworkEvent(Event):
    """Base class for all network events from the server."""

    pass


@dataclass(frozen=True)
class QueueUpdateEvent(NetworkEvent):
    """Matchmaking queue status update."""

    message: str


@dataclass(frozen=True)
class MatchFoundEvent(NetworkEvent):
    """Match has been found, game is starting."""

    player_id: PlayerID
    initial_round_start_pb: Any  # Protobuf RoundStartData


@dataclass(frozen=True)
class RoundStartEvent(NetworkEvent):
    """New round is starting with simulation data."""

    round_start_pb: Any  # Protobuf RoundStartData


@dataclass(frozen=True)
class RoundResultEvent(NetworkEvent):
    """Round has ended with results."""

    lives_lost_player_A: int
    gold_earned_player_A: int
    lives_lost_player_B: int
    gold_earned_player_B: int
    total_lives_player_A: int
    total_gold_player_A: int
    total_lives_player_B: int
    total_gold_player_B: int


@dataclass(frozen=True)
class TowerPlacedEvent(NetworkEvent):
    """A tower was placed (could be by either player)."""

    player_id: PlayerID
    tower_type: str
    tile_row: int
    tile_col: int
    level: int = 1


@dataclass(frozen=True)
class OpponentDisconnectedEvent(NetworkEvent):
    """Opponent has disconnected from the match."""

    pass


# =============================================================================
# Client Action Events (User wants to do something -> needs server confirmation)
# =============================================================================


@dataclass(frozen=True)
class ClientActionEvent(Event):
    """Base class for client actions that may require server confirmation."""

    pass


@dataclass(frozen=True)
class RequestBuildTowerEvent(ClientActionEvent):
    """Request to build a tower at a specific location."""

    player_id: PlayerID
    tower_type: str
    tile_row: int
    tile_col: int
    level: int = 1
    # For rollback if server rejects
    was_empty: bool = True
    sprite_existed: bool = False


@dataclass(frozen=True)
class RequestSendUnitsEvent(ClientActionEvent):
    """Request to send units on a route."""

    player_id: PlayerID
    unit_type: str
    route: int
    spawn_tick: int = 0


@dataclass(frozen=True)
class RequestRoundAckEvent(ClientActionEvent):
    """Acknowledge that client finished rendering a round."""

    player_id: PlayerID
    round_number: int


# =============================================================================
# Server Response Events (Server confirms/rejects client actions)
# =============================================================================


@dataclass(frozen=True)
class ServerResponseEvent(Event):
    """Base class for server responses to client actions."""

    success: bool


@dataclass(frozen=True)
class BuildTowerResponseEvent(ServerResponseEvent):
    """Server response to a build tower request."""

    tile_row: int
    tile_col: int
    was_empty: bool = True
    sprite_existed: bool = False


@dataclass(frozen=True)
class SendUnitsResponseEvent(ServerResponseEvent):
    """Server response to a send units request."""

    total_gold: int | None = None


# =============================================================================
# UI Events (Local UI state changes, no server involvement)
# =============================================================================


@dataclass(frozen=True)
class UIEvent(Event):
    """Base class for UI-related events."""

    pass


@dataclass(frozen=True)
class ToggleBuildModeEvent(UIEvent):
    """Toggle tower build mode on/off."""

    enabled: bool


@dataclass(frozen=True)
class HoverTileChangedEvent(UIEvent):
    """Mouse is hovering over a different tile."""

    tile: tuple[int, int] | None  # (row, col) or None if not hovering


@dataclass(frozen=True)
class RouteHoverChangedEvent(UIEvent):
    """Mouse is hovering over a route button."""

    route: int | None  # Route number (1-5) or None if not hovering


# =============================================================================
# State Change Events (Game state mutations)
# =============================================================================


@dataclass(frozen=True)
class StateEvent(Event):
    """Base class for game state change events."""

    pass


@dataclass(frozen=True)
class GoldChangedEvent(StateEvent):
    """Player's gold has changed."""

    player_id: PlayerID
    new_gold: int
    delta: int = 0  # Positive for gain, negative for spend


@dataclass(frozen=True)
class LivesChangedEvent(StateEvent):
    """Player's lives have changed."""

    player_id: PlayerID
    new_lives: int
    delta: int = 0


@dataclass(frozen=True)
class PhaseChangedEvent(StateEvent):
    """Game phase has changed (preparation/combat)."""

    phase: Literal["preparation", "combat"]
    seconds_remaining: float


@dataclass(frozen=True)
class RoundChangedEvent(StateEvent):
    """Round number has changed."""

    round_number: int
