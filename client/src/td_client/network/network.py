from __future__ import annotations

import logging
import os
import threading
from collections.abc import Callable, Sequence

import grpc

# Expect generated stubs under td_shared after protoc step:
# python -m grpc_tools.protoc -I shared/src --python_out=shared/src --grpc_python_out=shared/src td_shared/game.proto
try:
    from td_shared.protobuf import game_pb2, game_pb2_grpc
except Exception as e:
    game_pb2 = None
    game_pb2_grpc = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None

logger = logging.getLogger(__name__)


class NetworkClient:
    """
    Non-blocking gRPC client with per-call threads to avoid blocking render loop.

    handles all network communication between the game client and the server.
    It uses gRPC for RPC calls and implements non-blocking operations to prevent
    network I/O from blocking the render loop.

    - Asynchronous RPC calls: All network operations run in background threads
    - Callback-based API: Results are delivered via callbacks instead of blocking
    - Server streaming: QueueForMatch uses server-streaming for continuous event updates
    - Error handling: Exceptions are caught and passed to callbacks as failure signals
    """

    def __init__(self, server_addr: str | None = None) -> None:
        if server_addr is None:
            server_addr = os.getenv("TD_SERVER_ADDR", "127.0.0.1:42069")
        if _IMPORT_ERROR is not None:
            raise RuntimeError(
                "gRPC stubs not found. Generate them from td_shared/game.proto before using NetworkClient."
            ) from _IMPORT_ERROR
        self._channel = grpc.insecure_channel(server_addr)
        self._stub = game_pb2_grpc.YourGameServiceStub(self._channel)

    def close(self) -> None:
        self._channel.close()

    def queue_for_match(
        self,
        *,
        player_name: str,
        on_match_found: Callable[[str, game_pb2.RoundStartData], None],
        on_queue_update: Callable[[str], None] | None = None,
        on_round_start: Callable[[game_pb2.RoundStartData], None] | None = None,
        on_round_result: Callable[[game_pb2.RoundResultData], None] | None = None,
        on_tower_placed: Callable[[game_pb2.TowerPlaced], None] | None = None,
        on_opponent_disconnected: Callable[[], None] | None = None,
    ) -> threading.Thread:
        """Start server-streaming QueueForMatch in a background thread."""

        def _worker() -> None:
            try:
                req = game_pb2.QueueRequest(player_name=player_name)
                for event in self._stub.QueueForMatch(req):
                    which = event.WhichOneof("event_type")

                    if which == "queue_update":
                        if on_queue_update is not None:
                            logger.debug("QueueUpdate: %s", event.queue_update.message)
                            on_queue_update(event.queue_update.message)
                    elif which == "match_found":
                        logger.info(
                            "MatchFound: you are %s", event.match_found.player_id
                        )
                        on_match_found(
                            event.match_found.player_id,
                            event.match_found.initial_round_start,
                        )
                    elif which == "round_start" and on_round_start is not None:
                        logger.info("RoundStart received")
                        on_round_start(event.round_start)
                    elif which == "round_result" and on_round_result is not None:
                        logger.info(
                            "RoundResult received: A -%d +%d, B -%d +%d",
                            event.round_result.lives_lost_player_A,
                            event.round_result.gold_earned_player_A,
                            event.round_result.lives_lost_player_B,
                            event.round_result.gold_earned_player_B,
                        )
                        on_round_result(event.round_result)
                    elif which == "tower_placed" and on_tower_placed is not None:
                        logger.info(
                            "TowerPlaced received: %s at (%d,%d)",
                            event.tower_placed.player_id,
                            event.tower_placed.tile_row,
                            event.tower_placed.tile_col,
                        )
                        on_tower_placed(event.tower_placed)
                    elif (
                        which == "opponent_disconnected"
                        and on_opponent_disconnected is not None
                    ):
                        logger.info("OpponentDisconnected event received from server.")
                        on_opponent_disconnected()
            except Exception:
                # Swallow errors for now; caller can time out or retry
                logger.exception("QueueForMatch stream error")

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def build_tower(
        self,
        *,
        player_id: str,
        tower_type: str,
        tile_row: int,
        tile_col: int,
        level: int = 1,
        on_done: Callable[[bool], None] | None = None,
    ) -> threading.Thread:
        """Invoke BuildTower in a background thread; calls on_done(success) if provided."""

        def _worker() -> None:
            try:
                req = game_pb2.BuildTowerRequest(
                    player_id=player_id,
                    tower_type=tower_type,
                    tile_row=tile_row,
                    tile_col=tile_col,
                    level=level,
                )

                resp = self._stub.BuildTower(req)
                if on_done is not None:
                    on_done(bool(resp.success))

            except Exception:
                if on_done is not None:
                    on_done(False)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def send_units(
        self,
        *,
        player_id: str,
        units: Sequence[dict],
        on_done: Callable[[bool, int | None], None] | None = None,
    ) -> threading.Thread:
        """Invoke SendUnits in a background thread; units must map to SimUnitData fields."""

        def _worker() -> None:
            try:
                sim_units = []
                for u in units:
                    sim_units.append(
                        game_pb2.SimUnitData(
                            player_id=u.get("player_id", player_id),
                            unit_type=u["unit_type"],
                            route=int(u["route"]),
                            spawn_tick=int(u["spawn_tick"]),
                        )
                    )

                req = game_pb2.SendUnitsRequest(player_id=player_id, units=sim_units)
                resp = self._stub.SendUnits(req)

                if on_done is not None:
                    on_done(
                        bool(resp.success),
                        int(resp.total_gold) if hasattr(resp, "total_gold") else None,
                    )
            except Exception:
                if on_done is not None:
                    on_done(False, None)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t

    def round_ack(
        self,
        *,
        player_id: str,
        round_number: int,
        on_done: Callable[[bool], None] | None = None,
    ) -> threading.Thread:
        """Invoke RoundAck in a background thread; tells server client finished rendering the round."""

        def _worker() -> None:
            try:
                req = game_pb2.RoundAckRequest(
                    player_id=player_id, round_number=round_number
                )
                resp = self._stub.RoundAck(req)
                if on_done is not None:
                    on_done(bool(resp.success))
            except Exception:
                if on_done is not None:
                    on_done(False)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
