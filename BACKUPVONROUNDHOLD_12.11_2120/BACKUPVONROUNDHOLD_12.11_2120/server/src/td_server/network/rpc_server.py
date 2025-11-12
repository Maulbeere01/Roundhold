from __future__ import annotations

import logging
import time
from concurrent import futures
import threading
from typing import Optional

import grpc

from ..core.game_state_manager import GameStateManager
from ..core.round_manager import RoundManager
from td_shared.protobuf import game_pb2, game_pb2_grpc, sim_data_to_proto
from td_shared.game import SimulationData as SimDataDict, ROUND_ACK_TIMEOUT


class GameRpcServer(game_pb2_grpc.YourGameServiceServicer):
    """gRPC servicer backed by a shared GameStateManager."""

    def __init__(self, game_manager: GameStateManager, round_manager: RoundManager) -> None:
        self.game_manager = game_manager
        self.round_manager = round_manager
        self._log = logging.getLogger(__name__)
        self._round_thread_started = False
        self._match_lock = threading.Lock()
        self._waiting_clients: list[tuple[str, threading.Event, list[game_pb2.MatchEvent]]] = []
        # entries: (player_name, ready_event, outbox); outbox will be consumed by stream
        self._round_ack_lock = threading.Lock()
        self._round_acks: dict[int, set[str]] = {} # set of player_ids who acked

    def _ensure_round_loop(self) -> None:
        if not self._round_thread_started:
            threading.Thread(target=self.round_manager.run_game_loop, daemon=True).start()
            self._round_thread_started = True
            self._log.info("RoundManager thread started on first match")

    def BuildTower(self, request: game_pb2.BuildTowerRequest, context: grpc.ServicerContext) -> game_pb2.BuildTowerResponse:  # type: ignore[override]
        """Place a tower."""
        # Enforce no building in combat phase
        if not self.round_manager.is_in_preparation():
            self._log.info("BuildTower rejected: not in preparation phase")
            return game_pb2.BuildTowerResponse(success=False)
        
        placed = self.game_manager.build_tower(
            player_id=request.player_id,
            tower_type=request.tower_type,
            tile_row=int(request.tile_row),
            tile_col=int(request.tile_col),
            level=int(request.level) if request.level else 1,
        )
        success = placed is not None
        if success:
            # Broadcast TowerPlaced event to both clients immediately
            event = game_pb2.MatchEvent(
                tower_placed=game_pb2.TowerPlaced(
                    player_id=request.player_id,
                    tower_type=request.tower_type,
                    tile_row=int(request.tile_row),
                    tile_col=int(request.tile_col),
                    level=int(request.level) if request.level else 1,
                )
            )
            # Push to active clients' outboxes
            for ev, outbox in getattr(self.round_manager, "_active_clients", []):
                outbox.append(event)
                ev.set()
            self._log.info("Broadcasted TowerPlaced for player=%s at (%d,%d)", request.player_id, request.tile_row, request.tile_col)
        return game_pb2.BuildTowerResponse(success=success)

    def SendUnits(self, request: game_pb2.SendUnitsRequest, context: grpc.ServicerContext) -> game_pb2.SendUnitsResponse:  # type: ignore[override]
        """Queue units for the next wave."""
        try:
            if not self.round_manager.is_in_preparation():
                self._log.info("SendUnits rejected: not in preparation phase")
                # Return current gold so client can stay in sync
                current_gold = self.game_manager.get_player_gold(request.player_id)
                return game_pb2.SendUnitsResponse(success=False, total_gold=current_gold)
            units = [
                {
                    "player_id": u.player_id,
                    "unit_type": u.unit_type,
                    "route": int(u.route),
                    "spawn_tick": int(u.spawn_tick),
                }
                for u in request.units
            ]
            ok = self.game_manager.add_units_to_wave(request.player_id, units)  # type: ignore[arg-type]
            current_gold = self.game_manager.get_player_gold(request.player_id)
            if ok:
                self._log.info("SendUnits accepted: player=%s, count=%d", request.player_id, len(units))
                return game_pb2.SendUnitsResponse(success=True, total_gold=current_gold)
            else:
                self._log.info("SendUnits rejected (gold insuff.): player=%s", request.player_id)
                return game_pb2.SendUnitsResponse(success=False, total_gold=current_gold)
        except Exception:
            self._log.exception("SendUnits error")
            current_gold = self.game_manager.get_player_gold(request.player_id)
            return game_pb2.SendUnitsResponse(success=False, total_gold=current_gold)

    def QueueForMatch(self, request: game_pb2.QueueRequest, context: grpc.ServicerContext):
        """Server-streaming matchmaking: enqueue, send updates, then stream round events persistently."""
        player_name = request.player_name or "Player"
        ready = threading.Event()
        outbox: list[game_pb2.MatchEvent] = []
        with self._match_lock:
            self._log.info("QueueForMatch: %s joined queue", player_name)
            self._waiting_clients.append((player_name, ready, outbox))
            if len(self._waiting_clients) >= 2:
                (p1, e1, o1) = self._waiting_clients.pop(0)
                (p2, e2, o2) = self._waiting_clients.pop(0)
                # Assign roles
                player_A_name, player_B_name = p1, p2
                # Prepare initial snapshot
                sim_data_dict: SimDataDict = self.game_manager.get_current_state_snapshot()
                sim_proto = sim_data_to_proto(sim_data_dict)
                round_start = game_pb2.RoundStartData(simulation_data=sim_proto)
                # Enqueue MatchFound events
                o1.append(game_pb2.MatchEvent(match_found=game_pb2.MatchFound(
                    player_id="A", opponent_name=player_B_name, initial_round_start=round_start
                )))
                o2.append(game_pb2.MatchEvent(match_found=game_pb2.MatchFound(
                    player_id="B", opponent_name=player_A_name, initial_round_start=round_start
                )))
                self._log.info("MatchFound: A=%s, B=%s", player_A_name, player_B_name)
                e1.set()
                e2.set()
                # Register active match clients for round push events
                self.round_manager.set_active_match([(e1, o1), (e2, o2)])
                # Start round loop lazily on first match
                self._ensure_round_loop()

        # Persistent stream loop: keep streaming until client disconnects
        try:
            # Phase 1: poll until matched
            while not ready.is_set():
                if not context.is_active():
                    return
                msg = "Waiting for another player..."
                self._log.debug("QueueForMatch: sending queue_update to %s: %s", player_name, msg)
                yield game_pb2.MatchEvent(queue_update=game_pb2.QueueUpdate(message=msg))
                if ready.wait(timeout=1.0):
                    break
            
            # Phase 2: stream events from outbox persistently
            while context.is_active():
                # Wait for new events (with timeout to check context periodically)
                ready.wait(timeout=1.0)
                # Drain outbox
                while outbox:
                    ev = outbox.pop(0)
                    which = ev.WhichOneof("event_type")
                    self._log.debug("QueueForMatch: delivering %s to %s", which, player_name)
                    yield ev
                ready.clear()
        finally:
            # If this client is still in waiting list and disconnects, remove it
            with self._match_lock:
                for i, (pn, ev, ob) in enumerate(self._waiting_clients):
                    if ev is ready and pn == player_name:
                        self._waiting_clients.pop(i)
                        break
            self._log.info("QueueForMatch: %s disconnected", player_name)

    def RoundAck(self, request: game_pb2.RoundAckRequest, context: grpc.ServicerContext) -> game_pb2.RoundAckResponse:  # type: ignore[override]
        """Client signals that it finished rendering the round."""
        player_id = request.player_id
        round_num = int(request.round_number)
        with self._round_ack_lock:
            if round_num not in self._round_acks:
                self._round_acks[round_num] = set()
            self._round_acks[round_num].add(player_id)
            self._log.info("RoundAck: player=%s, round=%d, total_acks=%d", player_id, round_num, len(self._round_acks[round_num]))
        return game_pb2.RoundAckResponse(success=True)

    def wait_for_round_acks(self, round_num: int, timeout: float = ROUND_ACK_TIMEOUT) -> bool:
        """Wait until both players A and B have acked the round, or timeout."""
        start = time.time()
        while time.time() - start < timeout:
            with self._round_ack_lock:
                acks = self._round_acks.get(round_num, set())
                if "A" in acks and "B" in acks:
                    self._log.info("RoundAck: round %d complete (both players acked)", round_num)
                    return True
            time.sleep(0.1)
        self._log.warning("RoundAck: round %d timed out (missing acks)", round_num)
        return False


def serve(
    *,
    host: str = "0.0.0.0",
    port: int = 42069,
    max_workers: int = 10,
    logger: Optional[logging.Logger] = None,
) -> grpc.Server:
    """Start gRPC server and RoundManager."""
    log = logger or logging.getLogger(__name__)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))

    # Init shared state and round manager
    game_manager = GameStateManager()
    round_manager = RoundManager(game_manager, logger=log)

    # Attach servicer
    rpc_server_instance = GameRpcServer(game_manager, round_manager)
    game_pb2_grpc.add_YourGameServiceServicer_to_server(rpc_server_instance, server)

    # Set bidirectional reference: RoundManager needs to wait for RoundAck from both clients  after combat phase. 
    # The RPC server receives RoundAck requests, so RoundManager calls
    # rpc_server.wait_for_round_acks() to block until both players signal they finished rendering
    round_manager.set_rpc_server(rpc_server_instance)

    server.add_insecure_port(f"{host}:{port}")
    server.start()
    log.info("gRPC server started on %s:%d", host, port)

    return server
