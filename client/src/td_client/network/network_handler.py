"""Network handler that listens to client action events and executes network calls.

This handler bridges the EventBus with the NetworkClient, ensuring that:
- All network calls are triggered by events, not direct calls
- Responses are published back as events
- The BuildController and other UI components don't need direct NetworkClient access
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from td_client.events import (
    EventBus,
    RequestBuildTowerEvent,
    RequestSendUnitsEvent,
    RequestRoundAckEvent,
    BuildTowerResponseEvent,
    SendUnitsResponseEvent,
)

if TYPE_CHECKING:
    from td_client.network import NetworkClient

logger = logging.getLogger(__name__)


class NetworkHandler:
    """Handles network requests triggered by events.
    
    Subscribes to client action events (RequestBuildTowerEvent, etc.)
    and executes the corresponding network calls via NetworkClient.
    Responses are published back to the EventBus.
    """

    def __init__(self, network_client: NetworkClient, event_bus: EventBus):
        self.network_client = network_client
        self.event_bus = event_bus
        self._subscriptions: list = []
        
        self._subscribe()

    def _subscribe(self) -> None:
        """Subscribe to all client action events."""
        self._subscriptions.append(
            self.event_bus.subscribe(RequestBuildTowerEvent, self._on_request_build_tower)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(RequestSendUnitsEvent, self._on_request_send_units)
        )
        self._subscriptions.append(
            self.event_bus.subscribe(RequestRoundAckEvent, self._on_request_round_ack)
        )
        logger.debug("NetworkHandler subscribed to client action events")

    def cleanup(self) -> None:
        """Unsubscribe from all events."""
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    def _on_request_build_tower(self, event: RequestBuildTowerEvent) -> None:
        """Handle build tower request by calling NetworkClient."""
        logger.debug(
            "NetworkHandler: BuildTower request for player=%s at (%d,%d)",
            event.player_id,
            event.tile_row,
            event.tile_col,
        )
        
        self.network_client.build_tower(
            player_id=event.player_id,
            tower_type=event.tower_type,
            tile_row=event.tile_row,
            tile_col=event.tile_col,
            level=event.level,
            on_done=lambda success: self._publish_build_response(
                success, event.tile_row, event.tile_col, event.was_empty, event.sprite_existed
            ),
        )

    def _publish_build_response(
        self, success: bool, row: int, col: int, was_empty: bool, sprite_existed: bool
    ) -> None:
        """Publish build tower response event."""
        self.event_bus.publish(
            BuildTowerResponseEvent(
                success=success,
                tile_row=row,
                tile_col=col,
                was_empty=was_empty,
                sprite_existed=sprite_existed,
            )
        )

    def _on_request_send_units(self, event: RequestSendUnitsEvent) -> None:
        """Handle send units request by calling NetworkClient."""
        logger.debug(
            "NetworkHandler: SendUnits request for player=%s, route=%d",
            event.player_id,
            event.route,
        )
        
        self.network_client.send_units(
            player_id=event.player_id,
            units=[
                {
                    "unit_type": event.unit_type,
                    "route": event.route,
                    "spawn_tick": event.spawn_tick,
                }
            ],
            on_done=self._publish_send_units_response,
        )

    def _publish_send_units_response(self, success: bool, total_gold: int | None) -> None:
        """Publish send units response event."""
        self.event_bus.publish(
            SendUnitsResponseEvent(success=success, total_gold=total_gold)
        )

    def _on_request_round_ack(self, event: RequestRoundAckEvent) -> None:
        """Handle round ack request by calling NetworkClient."""
        logger.debug(
            "NetworkHandler: RoundAck request for player=%s, round=%d",
            event.player_id,
            event.round_number,
        )
        
        self.network_client.round_ack(
            player_id=event.player_id,
            round_number=event.round_number,
        )
