from __future__ import annotations

import logging

import pygame
from td_client.assets import AssetLoader
from td_client.config import AssetPaths, GameSettings
from td_client.display import DisplayManager
from td_client.network import NetworkClient
from td_shared import (
    TOWER_STATS,
    PlacementGrid,
    PlayerID,
    RoundStartData,
)

from .game_states import MapState, PhaseState, PlayerState, SimulationState, UIState

logger = logging.getLogger(__name__)


class GameSimulation:
    """Running game: map, simulation, rendering, UI state."""

    def __init__(
        self,
        display_manager: DisplayManager,
        asset_loader: AssetLoader,
        asset_paths: AssetPaths,
        settings: GameSettings,
        player_id: PlayerID,
        network_client: NetworkClient,
    ):
        # Store dependencies only, no heavy initialization
        # GameFactory.create_game() will handle full initialization
        self.settings = settings
        self.asset_paths = asset_paths
        self.asset_loader = asset_loader
        self.display_manager = display_manager
        self.player_id: PlayerID = player_id
        self.network_client = network_client

        # Initialize state containers (will be populated by GameFactory)
        self.map_state = MapState()
        self.player_state = PlayerState()
        self.phase_state = PhaseState()
        self.ui_state = UIState()
        self.sim_state = SimulationState()

    # public API
    def get_player_grid(self, player_id: PlayerID) -> PlacementGrid:
        return (
            self.map_state.placement_grid_A
            if player_id == "A"
            else self.map_state.placement_grid_B
        )

    def load_round_start(self, round_start: RoundStartData) -> None:
        self.player_state.current_round += 1
        logger.info("Loading RoundStart for round %d", self.player_state.current_round)
        self._clear_local_towers()
        self.player_state.round_result_received = False
        self.player_state.round_ack_sent = False
        self.player_state.round_base_my_lives = self.player_state.my_lives
        self.player_state.round_base_opponent_lives = self.player_state.opponent_lives
        self.phase_state.in_preparation = False
        self.phase_state.in_combat = True
        self.phase_state.combat_seconds_remaining = (
            self.phase_state.combat_seconds_total
        )
        self.sim_state.wave_simulator.load_wave(round_start["simulation_data"])

    def load_initial_round_preview(self, round_start: RoundStartData) -> None:
        logger.info("Loading initial preview snapshot (no round increment)")
        self.sim_state.wave_simulator.load_wave(round_start["simulation_data"])

    def handle_event(self, event: pygame.event.Event) -> None:
        self.sim_state.input_controller.handle_event(event, self)

    def update(self, dt: float) -> None:
        """Update simulation, visuals, timers and RoundAck logic."""
        # 1. Core Simulation Updates
        self.sim_state.wave_simulator.update(dt)
        self.sim_state.render_manager.update(dt)

        # 2. State Synchronization & Visuals
        self._sync_visuals_and_lives()

        # 3. Timer Logic
        self._update_phase_timers(dt)

        # 4. Network / Game Flow Logic
        self._check_and_send_round_ack()

    def _sync_visuals_and_lives(self) -> None:
        """Sync sprites and calculate visual life interpolation."""
        state = self.sim_state.wave_simulator.game_state
        if not state:
            return

        self.sim_state.render_manager.sync_sprites_to_state(state)

        if not self.player_state.round_result_received:
            self._update_interpolated_lives(state)

    def _update_interpolated_lives(self, state) -> None:
        """Calculate visual lives based on simulation state."""
        # Extract lives lost from simulation state
        lost_a = int(getattr(state, "lives_lost_player_A", 0))
        lost_b = int(getattr(state, "lives_lost_player_B", 0))

        base_lives = self.player_state.round_base_my_lives
        base_opp = self.player_state.round_base_opponent_lives

        if self.player_id == "A":
            self.player_state.my_lives = max(0, base_lives - lost_a)
            self.player_state.opponent_lives = max(0, base_opp - lost_b)
        else:
            self.player_state.my_lives = max(0, base_lives - lost_b)
            self.player_state.opponent_lives = max(0, base_opp - lost_a)

    def _update_phase_timers(self, dt: float) -> None:
        """Handle countdowns for prep and combat phases."""
        phase = self.phase_state

        if phase.in_preparation:
            phase.prep_seconds_remaining = max(0.0, phase.prep_seconds_remaining - dt)
            if phase.prep_seconds_remaining <= 0.0:
                phase.in_preparation = False

        if phase.in_combat:
            phase.combat_seconds_remaining = max(
                0.0, phase.combat_seconds_remaining - dt
            )

    def _check_and_send_round_ack(self) -> None:
        """Check if round is complete locally and notify server."""
        if not self.phase_state.in_combat:
            return

        state = self.sim_state.wave_simulator.game_state
        if (
            state
            and not self.player_state.round_ack_sent
            and self.player_state.current_round > 0
            and state.is_simulation_complete()
        ):
            logger.info(
                "Simulation complete for round %d, sending RoundAck",
                self.player_state.current_round,
            )
            self.network_client.round_ack(
                player_id=self.player_id,
                round_number=self.player_state.current_round,
            )
            self.player_state.round_ack_sent = True

    def render(self) -> None:
        """Draw world and HUD onto the render surface."""
        self.sim_state.render_manager.draw(self.map_state.terrain_map)
        self.sim_state.hud_renderer.render(self)

    # helpers for tower rollbacks & send_units
    def _remove_local_tower(self, player_id: str, row: int, col: int) -> None:
        self.sim_state.build_controller.remove_tower(player_id, row, col)

    def _clear_local_towers(self) -> None:
        for sprite in self.ui_state.local_towers.values():
            sprite.kill()
        self.ui_state.local_towers.clear()

    # network callbacks
    def _on_build_response(
        self,
        success: bool,
        *,
        row: int,
        col: int,
        was_empty: bool,
        sprite_existed: bool,
    ) -> None:
        if success:
            logger.info("BuildTower succeeded at (%d,%d)", row, col)
            return

        # Server rejected: Rollback
        logger.warning("BuildTower rejected at (%d,%d), rolling back", row, col)
        self._rollback_tower_build(row, col, was_empty, sprite_existed)

    def _rollback_tower_build(
        self, row: int, col: int, was_empty: bool, sprite_existed: bool
    ) -> None:
        """Revert local state after failed build."""
        # Refund gold
        tower_cost = int(TOWER_STATS["standard"]["cost"])
        self.player_state.my_gold += tower_cost

        # Remove sprite if we created a new one
        if not sprite_existed:
            self._remove_local_tower(self.player_id, row, col)

        # Clear grid if it was empty before
        if was_empty:
            grid = self.get_player_grid(self.player_id)
            grid.clear_tower(row, col)

    def _on_send_units_response(self, success: bool, total_gold: int | None) -> None:
        if success and total_gold is not None:
            logger.info("SendUnits acknowledged, updating gold to %d", total_gold)
            self.player_state.my_gold = int(total_gold)
        elif not success and total_gold is not None:
            self.player_state.my_gold = int(total_gold)
