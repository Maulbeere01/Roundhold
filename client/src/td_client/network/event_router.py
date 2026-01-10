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
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert round_start_pb is not None, "round_start_pb must not be None"
        assert hasattr(
            round_start_pb, "simulation_data"
        ), "round_start_pb must have simulation_data"

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
        # Preconditions
        assert round_start_pb is not None, "round_start_pb must not be None"
        assert hasattr(
            round_start_pb, "simulation_data"
        ), "round_start_pb must have simulation_data"

        self.event_bus.publish(RoundStartEvent(round_start_pb=round_start_pb))

    def on_round_result(self, round_result_pb) -> None:
        """Handle round result event from server."""
        # Preconditions
        assert round_result_pb is not None, "round_result_pb must not be None"
        assert hasattr(
            round_result_pb, "lives_lost_player_A"
        ), "round_result_pb must have lives_lost_player_A"
        assert hasattr(
            round_result_pb, "gold_earned_player_A"
        ), "round_result_pb must have gold_earned_player_A"
        assert hasattr(
            round_result_pb, "lives_lost_player_B"
        ), "round_result_pb must have lives_lost_player_B"
        assert hasattr(
            round_result_pb, "gold_earned_player_B"
        ), "round_result_pb must have gold_earned_player_B"
        assert hasattr(
            round_result_pb, "total_lives_player_A"
        ), "round_result_pb must have total_lives_player_A"
        assert hasattr(
            round_result_pb, "total_gold_player_A"
        ), "round_result_pb must have total_gold_player_A"
        assert hasattr(
            round_result_pb, "total_lives_player_B"
        ), "round_result_pb must have total_lives_player_B"
        assert hasattr(
            round_result_pb, "total_gold_player_B"
        ), "round_result_pb must have total_gold_player_B"

        lives_lost_A = int(round_result_pb.lives_lost_player_A)
        lives_lost_B = int(round_result_pb.lives_lost_player_B)
        gold_earned_A = int(round_result_pb.gold_earned_player_A)
        gold_earned_B = int(round_result_pb.gold_earned_player_B)
        total_lives_A = int(round_result_pb.total_lives_player_A)
        total_lives_B = int(round_result_pb.total_lives_player_B)
        total_gold_A = int(round_result_pb.total_gold_player_A)
        total_gold_B = int(round_result_pb.total_gold_player_B)

        # Data consistency checks
        assert (
            lives_lost_A >= 0
        ), f"lives_lost_player_A must be >= 0, not {lives_lost_A}"
        assert (
            lives_lost_B >= 0
        ), f"lives_lost_player_B must be >= 0, not {lives_lost_B}"
        assert (
            gold_earned_A >= 0
        ), f"gold_earned_player_A must be >= 0, not {gold_earned_A}"
        assert (
            gold_earned_B >= 0
        ), f"gold_earned_player_B must be >= 0, not {gold_earned_B}"
        assert (
            total_lives_A >= 0
        ), f"total_lives_player_A must be >= 0, not {total_lives_A}"
        assert (
            total_lives_B >= 0
        ), f"total_lives_player_B must be >= 0, not {total_lives_B}"
        assert (
            total_gold_A >= 0
        ), f"total_gold_player_A must be >= 0, not {total_gold_A}"
        assert (
            total_gold_B >= 0
        ), f"total_gold_player_B must be >= 0, not {total_gold_B}"

        self.event_bus.publish(
            RoundResultEvent(
                lives_lost_player_A=lives_lost_A,
                gold_earned_player_A=gold_earned_A,
                lives_lost_player_B=lives_lost_B,
                gold_earned_player_B=gold_earned_B,
                total_lives_player_A=total_lives_A,
                total_gold_player_A=total_gold_A,
                total_lives_player_B=total_lives_B,
                total_gold_player_B=total_gold_B,
            )
        )

    def on_tower_placed(self, tower_placed_pb) -> None:
        """Handle tower placed event from server."""
        # Preconditions
        assert tower_placed_pb is not None, "tower_placed_pb must not be None"
        assert hasattr(
            tower_placed_pb, "player_id"
        ), "tower_placed_pb must have player_id"
        assert hasattr(
            tower_placed_pb, "tower_type"
        ), "tower_placed_pb must have tower_type"
        assert hasattr(
            tower_placed_pb, "tile_row"
        ), "tower_placed_pb must have tile_row"
        assert hasattr(
            tower_placed_pb, "tile_col"
        ), "tower_placed_pb must have tile_col"

        player_id = tower_placed_pb.player_id
        tower_type = tower_placed_pb.tower_type
        tile_row = int(tower_placed_pb.tile_row)
        tile_col = int(tower_placed_pb.tile_col)
        level = int(tower_placed_pb.level) if tower_placed_pb.level else 1

        # Data consistency checks
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert (
            isinstance(tower_type, str) and tower_type
        ), "tower_type must be a non-empty string"
        assert tile_row >= 0, f"tile_row must be >= 0, not {tile_row}"
        assert tile_col >= 0, f"tile_col must be >= 0, not {tile_col}"
        assert level >= 1, f"level must be >= 1, not {level}"

        self.event_bus.publish(
            TowerPlacedEvent(
                player_id=player_id,
                tower_type=tower_type,
                tile_row=tile_row,
                tile_col=tile_col,
                level=level,
            )
        )

    def on_opponent_disconnected(self) -> None:
        """Handle opponent disconnected event."""
        logger.info(
            "Opponent disconnected, publishing event and switching to VictoryScreen"
        )
        self.event_bus.publish(OpponentDisconnectedEvent())
        self.app.switch_screen("GAME_OVER", won=True, reason="Opponent Left")
