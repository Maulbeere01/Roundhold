from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared import (
    TOWER_STATS,
    PlacementGrid,
    PlayerID,
    RoundStartData,
)

from ..assets import AssetLoader
from ..config import AssetPaths, GameSettings
from ..display import DisplayManager
from ..network import NetworkClient
from ..events import RequestRoundAckEvent
from .game_states import MapState, PhaseState, PlayerState, SimulationState, UIState

if TYPE_CHECKING:
    from ..events import EventBus

logger = logging.getLogger(__name__)


class GameSimulation:
    """
    Client-side game runtime responsible for rendering, input handling,
    local tower state, and synchronizing simulation snapshots from the server.

    This class does NOT own game logic or round progression; the server provides
    all authoritative state. GameSimulation focuses solely on:
    - maintaining local UI/game state (gold, lives, timers)
    - updating and rendering the wave simulation
    - applying server events (RoundStart, RoundResult, TowerPlaced)
    - delegating input to controllers (build, unit sending)
    - managing sprites, terrain, and placement grids

    In short: the visual and interactive layer of a round, not the game rules.
    """

    def __init__(
        self,
        display_manager: DisplayManager,
        asset_loader: AssetLoader,
        asset_paths: AssetPaths,
        settings: GameSettings,
        player_id: PlayerID,
        network_client: NetworkClient,
        event_bus: EventBus | None = None,
    ):
        # Store dependencies only, no heavy initialization
        # GameFactory.create_game() will handle full initialization
        self.settings = settings
        self.asset_paths = asset_paths
        self.asset_loader = asset_loader
        self.display_manager = display_manager
        self.player_id: PlayerID = player_id
        self.network_client = network_client
        self.event_bus = event_bus

        # Initialize state containers (will be populated by GameFactory)
        self.map_state = MapState()
        self.player_state = PlayerState()
        self.phase_state = PhaseState()
        self.ui_state = UIState()
        self.sim_state = SimulationState()

    # =========================================================================
    # Convenience properties for backwards compatibility
    # These delegate to the appropriate state container
    # =========================================================================

    @property
    def terrain_map(self):
        """Access terrain map from map_state."""
        return self.map_state.terrain_map

    @property
    def my_gold(self) -> int:
        """Access player gold from player_state."""
        return self.player_state.my_gold

    @my_gold.setter
    def my_gold(self, value: int) -> None:
        self.player_state.my_gold = value

    @property
    def my_lives(self) -> int:
        """Access player lives from player_state."""
        return self.player_state.my_lives

    @my_lives.setter
    def my_lives(self, value: int) -> None:
        self.player_state.my_lives = value

    @property
    def tower_build_mode(self) -> bool:
        """Access tower build mode from ui_state."""
        return self.ui_state.tower_build_mode

    @tower_build_mode.setter
    def tower_build_mode(self, value: bool) -> None:
        self.ui_state.tower_build_mode = value

    @property
    def hover_tile(self) -> tuple[int, int] | None:
        """Access hover tile from ui_state."""
        return self.ui_state.hover_tile

    @hover_tile.setter
    def hover_tile(self, value: tuple[int, int] | None) -> None:
        self.ui_state.hover_tile = value

    @property
    def tower_button(self):
        """Access tower button rect from ui_state."""
        return self.ui_state.tower_button

    @property
    def barracks_buttons(self):
        """Access barracks buttons from ui_state."""
        return self.ui_state.barracks_buttons

    @property
    def _local_towers(self):
        """Access local towers dict from ui_state."""
        return self.ui_state.local_towers

    @property
    def render_manager(self):
        """Access render manager from sim_state."""
        return self.sim_state.render_manager

    # =========================================================================
    # Public API
    # =========================================================================
    def get_player_grid(self, player_id: PlayerID) -> PlacementGrid:
        grid = self.map_state.placement_grid
        if grid is None:
            raise RuntimeError(
                f"Placement grid for player {player_id} is not initialized"
            )
        return grid

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
        self.sim_state.wave_simulator.update(dt)
        self.sim_state.render_manager.update(dt)

        state = self.sim_state.wave_simulator.game_state
        if state:
            self.sim_state.render_manager.sync_sprites_to_state(state)
            if not self.player_state.round_result_received:
                if self.player_id == "A":
                    my_vis = self.player_state.round_base_my_lives - int(
                        getattr(state, "lives_lost_player_A", 0)
                    )
                    opp_vis = self.player_state.round_base_opponent_lives - int(
                        getattr(state, "lives_lost_player_B", 0)
                    )
                else:
                    my_vis = self.player_state.round_base_my_lives - int(
                        getattr(state, "lives_lost_player_B", 0)
                    )
                    opp_vis = self.player_state.round_base_opponent_lives - int(
                        getattr(state, "lives_lost_player_A", 0)
                    )
                self.player_state.my_lives = max(0, my_vis)
                self.player_state.opponent_lives = max(0, opp_vis)

        if self.phase_state.in_preparation:
            self.phase_state.prep_seconds_remaining = max(
                0.0, self.phase_state.prep_seconds_remaining - dt
            )
            if self.phase_state.prep_seconds_remaining <= 0.0:
                self.phase_state.in_preparation = False

        if self.phase_state.in_combat:
            self.phase_state.combat_seconds_remaining = max(
                0.0, self.phase_state.combat_seconds_remaining - dt
            )
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
                # Publish event instead of calling network directly
                if self.event_bus:
                    self.event_bus.publish(
                        RequestRoundAckEvent(
                            player_id=self.player_id,
                            round_number=self.player_state.current_round,
                        )
                    )
                self.player_state.round_ack_sent = True

    def render(self) -> None:
        """Draw world and HUD onto the render surface."""
        self.sim_state.render_manager.draw(self.map_state.terrain_map)
        self.sim_state.hud_renderer.render(self)

    def cleanup(self) -> None:
        """Clean up resources when the game simulation is destroyed."""
        self._clear_local_towers()
        logger.info("GameSimulation cleaned up")

    # helpers for tower management
    def _clear_local_towers(self) -> None:
        """Remove all locally-spawned tower sprites."""
        for sprite in self.ui_state.local_towers.values():
            sprite.kill()
        self.ui_state.local_towers.clear()
