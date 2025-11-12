from __future__ import annotations

import logging
import threading
import time
from typing import Optional, List, Tuple

from .combat_sim import run_combat_simulation
from .game_state_manager import GameStateManager
from td_shared.game import RoundResultData, SimulationData, PREP_SECONDS, ROUND_ACK_TIMEOUT
from td_shared.protobuf import game_pb2, sim_data_to_proto


class RoundManager:
    """Timer-driven round controller (prepare -> combat -> repeat)."""

    def __init__(
        self,
        game_manager: GameStateManager,
        *,
        prepare_duration_seconds: int = int(PREP_SECONDS),
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.game_manager = game_manager
        self.prepare_duration_seconds = prepare_duration_seconds
        self._log = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        # Active match clients: list of (event, outbox)
        self._active_clients: List[Tuple[threading.Event, List[game_pb2.MatchEvent]]] = []
        self._phase_lock = threading.Lock()
        self._in_preparation: bool = False
        self._current_round: int = 0
        self._rpc_server = None  # Will be set by serve() to enable wait_for_round_acks
        self._pending_round_result: Optional[RoundResultData] = None

    def stop(self) -> None:
        self._stop_event.set()

    def set_active_match(self, clients: List[Tuple[threading.Event, List[game_pb2.MatchEvent]]]) -> None:
        """Register the two clients participating in the current/next round"""
        self._active_clients = clients
        self._log.info("RoundManager: active_clients set: %d", len(self._active_clients))

    def set_rpc_server(self, rpc_server) -> None:
        """Set reference to RPC server for wait_for_round_acks"""
        self._rpc_server = rpc_server

    def run_game_loop(self) -> None:
        """Main loop: alternates between preparation and combat phases"""
        self._log.info("RoundManager loop started (prep %ss)", self.prepare_duration_seconds)
        while not self._stop_event.is_set():
            self._current_round += 1
            with self._phase_lock:
                self._in_preparation = True
            self._log.info("Preparation phase started (round %d)", self._current_round)
            remaining = float(self.prepare_duration_seconds)
            while remaining > 0.0 and not self._stop_event.is_set():
                step = min(0.5, remaining)
                time.sleep(step)
                remaining -= step
            if self._stop_event.is_set():
                break
            self._log.info("Preparation phase ended (round %d)", self._current_round)

            # Only proceed if we have exactly two active clients matched
            if not self._active_clients or len(self._active_clients) < 2:
                self._log.info("RoundManager: no active match (clients=%d), skipping round", len(self._active_clients))
                # Continue to next preparation phase
                continue

            snapshot: SimulationData = self.game_manager.get_current_state_snapshot()
            self._log.debug("RoundStart snapshot prepared: %d towers, %d units",
                            len(snapshot["towers"]), len(snapshot["units"]))

            # Push RoundStart to active clients (if any)
            if self._active_clients:
                proto_sim = sim_data_to_proto(snapshot)
                start_event = game_pb2.MatchEvent(round_start=game_pb2.RoundStartData(simulation_data=proto_sim))
                for ev, outbox in self._active_clients:
                    outbox.append(start_event)
                    ev.set()
                self._log.info("RoundManager: pushed RoundStart to %d clients (round %d)", len(self._active_clients), self._current_round)

            with self._phase_lock:
                self._in_preparation = False
            worker = threading.Thread(
                target=self._run_combat_and_callback, args=(snapshot,), daemon=True
            )
            worker.start()

            worker.join()

            # Wait for both clients to acknowledge they finished rendering the round
            if self._rpc_server:
                self._log.info("Waiting for RoundAcks (round %d)...", self._current_round)
                self._rpc_server.wait_for_round_acks(self._current_round, timeout=ROUND_ACK_TIMEOUT)
            else:
                # Fallback: just wait a fixed amount if no RPC server reference
                self._log.warning("No RPC server reference, using fixed 2s delay instead of RoundAck")
                time.sleep(2.0)

            # After ACKs, push RoundResult to clients (authoritative end-of-round results)
            if self._pending_round_result and self._active_clients:
                pr = self._pending_round_result
                rr = game_pb2.RoundResultData(
                    lives_lost_player_A=int(pr["lives_lost_player_A"]),
                    gold_earned_player_A=int(pr["gold_earned_player_A"]),
                    lives_lost_player_B=int(pr["lives_lost_player_B"]),
                    gold_earned_player_B=int(pr["gold_earned_player_B"]),
                    total_lives_player_A=self.game_manager.player_A_lives,
                    total_gold_player_A=self.game_manager.player_A_gold,
                    total_lives_player_B=self.game_manager.player_B_lives,
                    total_gold_player_B=self.game_manager.player_B_gold,
                )
                event = game_pb2.MatchEvent(round_result=rr)
                for ev, outbox in self._active_clients:
                    outbox.append(event)
                    ev.set()
                self._log.info("RoundManager: pushed RoundResult to %d clients (after ACKs)", len(self._active_clients))
                self._pending_round_result = None

        self._log.info("RoundManager game loop stopped")

    def _run_combat_and_callback(self, snapshot: SimulationData) -> None:
        """Worker that runs the simulation and applies results."""
        self._log.info("Combat phase started")
        result: RoundResultData = run_combat_simulation(snapshot)
        self._log.info(
            "Combat phase ended: A lost %d, B lost %d, A gold +%d, B gold +%d",
            result["lives_lost_player_A"],
            result["lives_lost_player_B"],
            result["gold_earned_player_A"],
            result["gold_earned_player_B"],
        )
        self.game_manager.apply_round_result(result)
        self.game_manager.clear_wave_data()
        # Defer RoundResult push until after ACKs
        self._pending_round_result = result

    def is_in_preparation(self) -> bool:
        with self._phase_lock:
            return self._in_preparation
