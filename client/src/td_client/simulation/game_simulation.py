from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared import (
    PlacementGrid,
    PlayerID,
    RoundStartData,
)

from client.src.td_client.audio.audio import AudioService

from ..assets import AssetLoader
from ..config import AssetPaths, GameSettings
from ..display import DisplayManager
from ..events import RequestRoundAckEvent
from ..network import NetworkClient
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
        audio: AudioService,
        event_bus: EventBus | None = None,
    ):
        # Preconditions
        assert display_manager is not None, "display_manager must not be None"
        assert asset_loader is not None, "asset_loader must not be None"
        assert asset_paths is not None, "asset_paths must not be None"
        assert settings is not None, "settings must not be None"
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert network_client is not None, "network_client must not be None"

        # Store dependencies only, no heavy initialization
        # GameFactory.create_game() will handle full initialization
        self.settings = settings
        self.asset_paths = asset_paths
        self.asset_loader = asset_loader
        self.display_manager = display_manager
        self.player_id: PlayerID = player_id
        self.network_client = network_client
        self.audio = audio
        self.event_bus = event_bus

        # Initialize state containers (will be populated by GameFactory)
        self.map_state = MapState()
        self.player_state = PlayerState()
        self.phase_state = PhaseState()
        self.ui_state = UIState()
        self.sim_state = SimulationState()

        # Postconditions
        assert self.player_id == player_id, "player_id not set correctly"
        assert self.map_state is not None, "map_state not initialized"
        assert self.player_state is not None, "player_state not initialized"
        assert self.phase_state is not None, "phase_state not initialized"
        assert self.ui_state is not None, "ui_state not initialized"
        assert self.sim_state is not None, "sim_state not initialized"

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
        # Preconditions
        assert round_start is not None, "round_start must not be None"
        assert "simulation_data" in round_start, "round_start must have simulation_data"
        assert (
            self.phase_state.in_preparation or self.player_state.current_round == 0
        ), "Should transition from preparation phase or be initial round"

        old_round = self.player_state.current_round
        self.player_state.current_round += 1
        logger.info("Loading RoundStart for round %d", self.player_state.current_round)

        # Postcondition: Round should increment
        assert (
            self.player_state.current_round == old_round + 1
        ), f"Round should increment by 1: expected {old_round + 1}, got {self.player_state.current_round}"

        # DON'T clear preview sprites yet - they'll fade out as units spawn
        # Just clear the queue data, not the actual sprites
        self.ui_state.route_unit_previews.clear()
        # DON'T reset _last_preview_state - this would trigger HUD to clear sprites

        # Reset the tracking for spawned units so previews can be cleared properly
        if hasattr(self.sim_state.render_manager, "_spawned_unit_ids"):
            self.sim_state.render_manager._spawned_unit_ids.clear()

        self._clear_local_towers()

        # Set gold mines to inactive during combat phase
        self._update_gold_mine_states(active=False)

        self.player_state.round_result_received = False
        self.player_state.round_ack_sent = False
        self.player_state.round_base_my_lives = self.player_state.my_lives
        self.player_state.round_base_opponent_lives = self.player_state.opponent_lives
        self.phase_state.in_preparation = False
        self.phase_state.in_combat = True
        self.phase_state.combat_seconds_remaining = (
            self.phase_state.combat_seconds_total
        )

        # Postconditions: Phase transition should be valid
        assert (
            not self.phase_state.in_preparation
        ), "Should not be in preparation after round start"
        assert self.phase_state.in_combat, "Should be in combat after round start"
        assert (
            self.phase_state.combat_seconds_remaining > 0
        ), f"combat_seconds_remaining must be > 0, not {self.phase_state.combat_seconds_remaining}"
        assert (
            self.player_state.my_lives >= 0
        ), f"my_lives must be >= 0, not {self.player_state.my_lives}"
        assert (
            self.player_state.opponent_lives >= 0
        ), f"opponent_lives must be >= 0, not {self.player_state.opponent_lives}"

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
            self.sim_state.render_manager.sync_sprites_to_state(state, self.ui_state)

            # Spawn arrow projectiles from simulation shots
            self.sim_state.render_manager.spawn_projectiles_from_state(
                state, self.ui_state
            )

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

                # Detect damage and trigger castle hit effects (only if castle still alive)
                if my_vis < self.player_state.my_lives and my_vis > 0:
                    # My castle was hit but still alive
                    castle = (
                        self.sim_state.render_manager.castle_A_sprite
                        if self.player_id == "A"
                        else self.sim_state.render_manager.castle_B_sprite
                    )
                    if castle and hasattr(castle, "trigger_hit_effect"):
                        castle.trigger_hit_effect()
                        # Spawn damage text at castle (only if castle is at valid position)
                        damage = self.player_state.my_lives - my_vis
                        if castle and castle.rect.centery > 50:
                            import time

                            self.ui_state.floating_damage_texts.append(
                                {
                                    "amount": damage,
                                    "x": castle.rect.centerx,
                                    "y": castle.rect.top - 20,
                                    "start_time": time.time(),
                                }
                            )

                if opp_vis < self.player_state.opponent_lives and opp_vis > 0:
                    # Opponent castle was hit but still alive
                    castle = (
                        self.sim_state.render_manager.castle_B_sprite
                        if self.player_id == "A"
                        else self.sim_state.render_manager.castle_A_sprite
                    )
                    if castle and hasattr(castle, "trigger_hit_effect"):
                        castle.trigger_hit_effect()
                        # Spawn damage text at castle (only if castle is at valid position)
                        damage = self.player_state.opponent_lives - opp_vis
                        if castle and castle.rect.centery > 50:
                            import time

                            self.ui_state.floating_damage_texts.append(
                                {
                                    "amount": damage,
                                    "x": castle.rect.centerx,
                                    "y": castle.rect.top - 20,
                                    "start_time": time.time(),
                                }
                            )

                self.player_state.my_lives = max(0, my_vis)
                self.player_state.opponent_lives = max(0, opp_vis)

                # Postconditions: Lives should be non-negative
                assert (
                    self.player_state.my_lives >= 0
                ), f"my_lives must be >= 0, not {self.player_state.my_lives}"
                assert (
                    self.player_state.opponent_lives >= 0
                ), f"opponent_lives must be >= 0, not {self.player_state.opponent_lives}"

        # Preconditions
        assert dt >= 0, f"dt must be >= 0, not {dt}"
        assert not (
            self.phase_state.in_preparation and self.phase_state.in_combat
        ), "Cannot be in both preparation and combat phase"

        if self.phase_state.in_preparation:
            old_prep_remaining = self.phase_state.prep_seconds_remaining
            self.phase_state.prep_seconds_remaining = max(
                0.0, self.phase_state.prep_seconds_remaining - dt
            )
            # Postcondition: Time should only decrease
            assert (
                self.phase_state.prep_seconds_remaining <= old_prep_remaining
            ), "prep_seconds_remaining should not increase"
            assert (
                self.phase_state.prep_seconds_remaining >= 0
            ), f"prep_seconds_remaining must be >= 0, not {self.phase_state.prep_seconds_remaining}"

            if self.phase_state.prep_seconds_remaining <= 0.0:
                self.phase_state.in_preparation = False
                # Postcondition: Should transition out of preparation
                assert (
                    not self.phase_state.in_preparation
                ), "Should not be in preparation after timer expires"

        if self.phase_state.in_combat:
            old_combat_remaining = self.phase_state.combat_seconds_remaining
            self.phase_state.combat_seconds_remaining = max(
                0.0, self.phase_state.combat_seconds_remaining - dt
            )
            # Postcondition: Time should only decrease
            assert (
                self.phase_state.combat_seconds_remaining <= old_combat_remaining
            ), "combat_seconds_remaining should not increase"
            assert (
                self.phase_state.combat_seconds_remaining >= 0
            ), f"combat_seconds_remaining must be >= 0, not {self.phase_state.combat_seconds_remaining}"
            state = self.sim_state.wave_simulator.game_state

            if self.player_state.my_lives <= 0:
                self.render_manager.destroy_castle(self.player_id)

            if self.player_state.opponent_lives <= 0:
                opponent_id = "B" if self.player_id == "A" else "A"
                self.render_manager.destroy_castle(opponent_id)

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
        self._clear_gold_mines()
        logger.info("GameSimulation cleaned up")

    # helpers for tower management
    def _clear_local_towers(self) -> None:
        """Remove all locally-spawned tower sprites."""
        list(map(lambda s: s.kill(), self.ui_state.local_towers.values()))
        self.ui_state.local_towers.clear()

    def _clear_gold_mines(self) -> None:
        """Remove all locally-spawned gold mine sprites."""
        list(map(lambda s: s.kill(), self.ui_state.local_gold_mines.values()))
        self.ui_state.local_gold_mines.clear()

    def _update_gold_mine_states(self, active: bool) -> None:
        """Update all gold mines to active or inactive state."""
        # Update locally placed gold mines
        for sprite in self.ui_state.local_gold_mines.values():
            if hasattr(sprite, "set_active"):
                sprite.set_active(active)

        # Also update simulation-side gold mines (opponent's mines)
        if hasattr(self.sim_state, "render_manager") and self.sim_state.render_manager:
            for (
                sprite
            ) in self.sim_state.render_manager.sprite_factory.tower_sprites.values():
                if hasattr(sprite, "set_active"):
                    sprite.set_active(active)
