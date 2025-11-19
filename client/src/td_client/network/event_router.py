from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .listener import NetworkListener

if TYPE_CHECKING:
    from td_client.main import GameApp

logger = logging.getLogger(__name__)


class NetworkEventRouter:
    """
    Central router for all network events, coming in via the QueueForMatch stream
    Dispatches events to the appropriate active screen.
    """

    def __init__(self, app: GameApp):
        self.app = app

    def on_queue_update(self, message: str) -> None:
        waiting = self.app.screens.get("WAITING")
        if waiting:
            waiting.set_message(message)

    def on_match_found(self, player_id: str, round_start_pb) -> None:
        logger.info("Match found. Assigned id=%s", player_id)
        self.app.switch_screen(
            "GAME",
            player_id=player_id,
            round_start_pb=round_start_pb,
        )

    def on_round_start(self, round_start_pb) -> None:
        screen = self.app.current_screen
        if isinstance(screen, NetworkListener):
            screen.on_round_start(round_start_pb)

    def on_round_result(self, round_result_pb) -> None:
        screen = self.app.current_screen
        if isinstance(screen, NetworkListener):
            screen.on_round_result(round_result_pb)

    def on_tower_placed(self, tower_placed_pb) -> None:
        screen = self.app.current_screen
        if isinstance(screen, NetworkListener):
            screen.on_tower_placed(tower_placed_pb)

    def on_opponent_disconnected(self) -> None:
        logger.info("Opponent disconnected, switching to VictoryScreen")
        self.app.switch_screen("VICTORY")
