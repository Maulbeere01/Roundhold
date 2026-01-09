from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from td_client.events import (
    EventBus,
    MatchFoundEvent,
    OpponentDisconnectedEvent,
    QueueUpdateEvent,
    RoundResultEvent,
    RoundStartEvent,
    TowerPlacedEvent,
)

if TYPE_CHECKING:
    from td_client.main import GameApp

logger = logging.getLogger(__name__)


class NetworkEventRouter:
    """
    Central router for all network events, coming in via the QueueForMatch stream.
    Publishes events to the central EventBus for decoupled handling.

    This class acts as the bridge between the gRPC network layer and the
    client's event-driven architecture. Network callbacks are converted
    to typed Event objects and published to the EventBus.
    """

    def __init__(self, app: GameApp, event_bus: EventBus):
        self.app = app
        self.event_bus = event_bus

    def on_queue_update(self, message: str) -> None:
        """Handle queue update from matchmaking."""
        self.event_bus.publish(QueueUpdateEvent(message=message))

    def on_match_found(self, player_id: str, round_start_pb) -> None:
        """Handle match found event - publishes to bus and switches screen."""
        logger.info("Match found. Assigned id=%s", player_id)
        self.event_bus.publish(
            MatchFoundEvent(player_id=player_id, initial_round_start_pb=round_start_pb)
        )
        # Screen switch still handled directly for now (could be event-driven later)
        self.app.switch_screen(
            "GAME",
            player_id=player_id,
            round_start_pb=round_start_pb,
        )

    def on_round_start(self, round_start_pb) -> None:
        """Handle round start event from server."""
        self.event_bus.publish(RoundStartEvent(round_start_pb=round_start_pb))

    def on_round_result(self, round_result_pb) -> None:
        """Handle round result event from server."""
        self.event_bus.publish(
            RoundResultEvent(
                lives_lost_player_A=int(round_result_pb.lives_lost_player_A),
                gold_earned_player_A=int(round_result_pb.gold_earned_player_A),
                lives_lost_player_B=int(round_result_pb.lives_lost_player_B),
                gold_earned_player_B=int(round_result_pb.gold_earned_player_B),
                total_lives_player_A=int(round_result_pb.total_lives_player_A),
                total_gold_player_A=int(round_result_pb.total_gold_player_A),
                total_lives_player_B=int(round_result_pb.total_lives_player_B),
                total_gold_player_B=int(round_result_pb.total_gold_player_B),
            )
        )

    def on_tower_placed(self, tower_placed_pb) -> None:
        """Handle tower placed event from server."""
        self.event_bus.publish(
            TowerPlacedEvent(
                player_id=tower_placed_pb.player_id,
                tower_type=tower_placed_pb.tower_type,
                tile_row=int(tower_placed_pb.tile_row),
                tile_col=int(tower_placed_pb.tile_col),
                level=int(tower_placed_pb.level) if tower_placed_pb.level else 1,
            )
        )

    def on_opponent_disconnected(self) -> None:
        """Handle opponent disconnected event."""
        logger.info(
            "Opponent disconnected, publishing event and switching to VictoryScreen"
        )
        self.event_bus.publish(OpponentDisconnectedEvent())
        self.app.switch_screen("GAME_OVER", won=True, reason="Opponent Left")
