from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared import PlayerID, RoundStartData, SimulationData, proto_to_sim_data

from ..network.listener import NetworkListener
from ..simulation.game_factory import GameFactory
from .base import Screen

if TYPE_CHECKING:
    from ..main import GameApp
    from ..simulation.game_simulation import GameSimulation

logger = logging.getLogger(__name__)


class GameScreen(Screen, NetworkListener):
    """Wraps GameSimulation and handles network callbacks."""

    def __init__(self, app: GameApp) -> None:
        super().__init__(app)
        self.game: GameSimulation | None = None
        self.player_id: PlayerID | None = None

    def enter(self, **kwargs) -> None:
        player_id = kwargs.get("player_id")
        round_start_pb = kwargs.get("round_start_pb")

        if player_id is None or round_start_pb is None:
            logger.error("GameScreen entered without player_id or round_start_pb")
            return

        logger.info("Entering GameScreen with player_id=%s", player_id)

        simulation_data: SimulationData = proto_to_sim_data(
            round_start_pb.simulation_data
        )
        round_start: RoundStartData = {"simulation_data": simulation_data}

        player_id_typed: PlayerID = player_id
        self.player_id = player_id_typed

        self.game = GameFactory.create_game(
            display_manager=self.app.display_manager,
            asset_loader=self.app.asset_loader,
            asset_paths=self.app.asset_paths,
            settings=self.app.settings,
            player_id=player_id_typed,
            network_client=self.app.network_client,
        )

        self.game.phase_state.in_preparation = True
        self.game.phase_state.in_combat = False
        self.game.phase_state.prep_seconds_remaining = (
            self.game.phase_state.prep_seconds_total
        )
        self.game.load_initial_round_preview(round_start)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.game:
            self.game.handle_event(event)

    def update(self, dt: float) -> None:
        if self.game:
            self.game.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self.game:
            self.game.render()

    # network-driven events
    def on_round_start(self, round_start_pb) -> None:
        if not self.game:
            return
        simulation_data: SimulationData = proto_to_sim_data(
            round_start_pb.simulation_data
        )
        round_start: RoundStartData = {"simulation_data": simulation_data}
        self.game.load_round_start(round_start)

    def on_round_result(self, round_result_pb) -> None:
        if not self.game or not self.player_id:
            return
        logger.info(
            "RoundResult: A -%d +%d, B -%d +%d (A %d lives/%d gold, B %d lives/%d gold)",
            round_result_pb.lives_lost_player_A,
            round_result_pb.gold_earned_player_A,
            round_result_pb.lives_lost_player_B,
            round_result_pb.gold_earned_player_B,
            round_result_pb.total_lives_player_A,
            round_result_pb.total_gold_player_A,
            round_result_pb.total_lives_player_B,
            round_result_pb.total_gold_player_B,
        )

        if self.player_id == "A":
            self.game.player_state.my_lives = int(round_result_pb.total_lives_player_A)
            self.game.player_state.my_gold = int(round_result_pb.total_gold_player_A)
            self.game.player_state.opponent_lives = int(
                round_result_pb.total_lives_player_B
            )
        else:
            self.game.player_state.my_lives = int(round_result_pb.total_lives_player_B)
            self.game.player_state.my_gold = int(round_result_pb.total_gold_player_B)
            self.game.player_state.opponent_lives = int(
                round_result_pb.total_lives_player_A
            )

        self.game.player_state.round_result_received = True
        self.game.phase_state.in_combat = False
        self.game.phase_state.in_preparation = True
        self.game.phase_state.prep_seconds_remaining = (
            self.game.phase_state.prep_seconds_total
        )

    def on_tower_placed(self, tower_placed_pb) -> None:
        if not self.game:
            return

        player_id = tower_placed_pb.player_id
        row = int(tower_placed_pb.tile_row)
        col = int(tower_placed_pb.tile_col)

        grid = self.game.get_player_grid(player_id)
        if grid.is_buildable(row, col):
            grid.place_tower(row, col)

        self.game.sim_state.build_controller.spawn_tower(
            player_id, row, col, "standard"
        )

    def on_opponent_disconnected(self) -> None:
        logger.info("Opponent disconnected. You win!")
        self.app.switch_screen("VICTORY")
