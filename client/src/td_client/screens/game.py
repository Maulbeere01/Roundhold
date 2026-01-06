from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared import PlayerID, RoundStartData, SimulationData, proto_to_sim_data

from td_client.events import (
    RoundResultEvent,
    RoundStartEvent,
    TowerPlacedEvent,
)

from ..simulation.game_factory import GameFactory
from .base import Screen

if TYPE_CHECKING:
    from ..main import GameApp
    from ..simulation.game_simulation import GameSimulation

logger = logging.getLogger(__name__)


class GameScreen(Screen):
    """Wraps GameSimulation and handles network events via EventBus."""

    def __init__(self, app: GameApp) -> None:
        super().__init__(app)
        self.game: GameSimulation | None = None
        self.player_id: PlayerID | None = None

    def _subscribe_events(self) -> None:
        """Subscribe to game-relevant events from the EventBus."""
        self._add_subscription(
            self.app.event_bus.subscribe(RoundStartEvent, self._on_round_start)
        )
        self._add_subscription(
            self.app.event_bus.subscribe(RoundResultEvent, self._on_round_result)
        )
        self._add_subscription(
            self.app.event_bus.subscribe(TowerPlacedEvent, self._on_tower_placed)
        )

    def enter(self, **kwargs) -> None:
        super().enter(**kwargs)

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
            event_bus=self.app.event_bus,
        )

        self.game.phase_state.in_preparation = True
        self.game.phase_state.in_combat = False
        self.game.phase_state.prep_seconds_remaining = (
            self.game.phase_state.prep_seconds_total
        )
        self.game.load_initial_round_preview(round_start)

    def exit(self) -> None:
        """Clean up game simulation when leaving screen."""
        super().exit()
        if self.game:
            self.game.cleanup()
            self.game = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.game:
            self.game.handle_event(event)

    def update(self, dt: float) -> None:
        if self.game:
            self.game.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self.game:
            self.game.render()

    # Event handlers (called via EventBus)
    def _on_round_start(self, event: RoundStartEvent) -> None:
        """Handle round start event from EventBus."""
        if not self.game:
            return
        simulation_data: SimulationData = proto_to_sim_data(
            event.round_start_pb.simulation_data
        )
        round_start: RoundStartData = {"simulation_data": simulation_data}
        self.game.load_round_start(round_start)

    def _on_round_result(self, event: RoundResultEvent) -> None:
        """Handle round result event from EventBus."""
        if not self.game or not self.player_id:
            return
        logger.info(
            "RoundResult: A -%d +%d, B -%d +%d (A %d lives/%d gold, B %d lives/%d gold)",
            event.lives_lost_player_A,
            event.gold_earned_player_A,
            event.lives_lost_player_B,
            event.gold_earned_player_B,
            event.total_lives_player_A,
            event.total_gold_player_A,
            event.total_lives_player_B,
            event.total_gold_player_B,
        )

        if self.player_id == "A":
            self.game.player_state.my_lives = event.total_lives_player_A
            self.game.player_state.my_gold = event.total_gold_player_A
            self.game.player_state.opponent_lives = event.total_lives_player_B
        else:
            self.game.player_state.my_lives = event.total_lives_player_B
            self.game.player_state.my_gold = event.total_gold_player_B
            self.game.player_state.opponent_lives = event.total_lives_player_A

        # 2. CHECK FOR GAME OVER
        my_lives = self.game.player_state.my_lives
        opp_lives = self.game.player_state.opponent_lives

        if my_lives <= 0:
            # I lost
            self.app.switch_screen("GAME_OVER", won=False)
        elif opp_lives <= 0:
            # I won
            self.app.switch_screen("GAME_OVER", won=True)
        else:
            # Nobody won next round begin
            self.game.player_state.round_result_received = True
            self.game.phase_state.in_combat = False
            self.game.phase_state.in_preparation = True
            self.game.phase_state.prep_seconds_remaining = (
                self.game.phase_state.prep_seconds_total
            )
            
            # Clear preview sprites when returning to preparation phase
            for sprite in self.game.ui_state.route_preview_sprites:
                sprite.kill()
                self.game.sim_state.render_manager.animation_manager.unregister(sprite)
            self.game.ui_state.route_preview_sprites.clear()
            if hasattr(self.game.ui_state, '_last_preview_state'):
                self.game.ui_state._last_preview_state = {}
            # Reset spawned unit tracking for next round
            if hasattr(self.game.sim_state.render_manager, '_spawned_unit_ids'):
                self.game.sim_state.render_manager._spawned_unit_ids.clear()

    def _on_tower_placed(self, event: TowerPlacedEvent) -> None:
        """Handle tower placed event from EventBus."""
        if not self.game:
            return

        grid = self.game.get_player_grid(event.player_id)
        if grid.is_buildable(event.tile_row, event.tile_col):
            grid.place_tower(event.tile_row, event.tile_col)

        self.game.sim_state.build_controller.spawn_tower(
            event.player_id, event.tile_row, event.tile_col, event.tower_type
        )
