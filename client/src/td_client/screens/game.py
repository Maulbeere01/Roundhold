from __future__ import annotations

import logging
from functools import reduce
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

        # Preconditions
        assert player_id is not None, "player_id must be provided"
        assert round_start_pb is not None, "round_start_pb must be provided"
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert hasattr(
            round_start_pb, "simulation_data"
        ), "round_start_pb must have simulation_data"

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
            audio=self.app.audio,
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
        # Ensure mines are turned off immediately when combat begins
        self.game._update_gold_mine_states(active=False)

    def _on_round_result(self, event: RoundResultEvent) -> None:
        """Handle round result event from EventBus."""
        # Preconditions
        assert event is not None, "event must not be None"
        assert (
            event.lives_lost_player_A >= 0
        ), f"lives_lost_player_A must be >= 0, not {event.lives_lost_player_A}"
        assert (
            event.lives_lost_player_B >= 0
        ), f"lives_lost_player_B must be >= 0, not {event.lives_lost_player_B}"
        assert (
            event.gold_earned_player_A >= 0
        ), f"gold_earned_player_A must be >= 0, not {event.gold_earned_player_A}"
        assert (
            event.gold_earned_player_B >= 0
        ), f"gold_earned_player_B must be >= 0, not {event.gold_earned_player_B}"
        assert (
            event.total_lives_player_A >= 0
        ), f"total_lives_player_A must be >= 0, not {event.total_lives_player_A}"
        assert (
            event.total_lives_player_B >= 0
        ), f"total_lives_player_B must be >= 0, not {event.total_lives_player_B}"
        assert (
            event.total_gold_player_A >= 0
        ), f"total_gold_player_A must be >= 0, not {event.total_gold_player_A}"
        assert (
            event.total_gold_player_B >= 0
        ), f"total_gold_player_B must be >= 0, not {event.total_gold_player_B}"

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

        # Clear any stray floating texts from combat
        self.game.ui_state.floating_gold_texts.clear()
        self.game.ui_state.floating_damage_texts.clear()

        if self.player_id == "A":
            self.game.player_state.my_lives = event.total_lives_player_A
            self.game.player_state.my_gold = event.total_gold_player_A
            self.game.player_state.opponent_lives = event.total_lives_player_B
        else:
            self.game.player_state.my_lives = event.total_lives_player_B
            self.game.player_state.my_gold = event.total_gold_player_B
            self.game.player_state.opponent_lives = event.total_lives_player_A

        # Postconditions: State should be updated correctly
        assert (
            self.game.player_state.my_lives >= 0
        ), f"my_lives must be >= 0, not {self.game.player_state.my_lives}"
        assert (
            self.game.player_state.opponent_lives >= 0
        ), f"opponent_lives must be >= 0, not {self.game.player_state.opponent_lives}"
        assert (
            self.game.player_state.my_gold >= 0
        ), f"my_gold must be >= 0, not {self.game.player_state.my_gold}"

        # Trigger gold flash when gold is received from round result
        gold_earned = (
            event.gold_earned_player_A
            if self.player_id == "A"
            else event.gold_earned_player_B
        )
        if gold_earned > 0:
            self.game.ui_state.gold_flash_timer = 0.5
            self.game.ui_state.gold_flash_color = (
                100,
                255,
                100,
            )  # Green flash for gain
            self.game.ui_state.gold_display_scale = 1.2

        # 2. CHECK FOR GAME OVER
        my_lives = self.game.player_state.my_lives
        opp_lives = self.game.player_state.opponent_lives

        if my_lives <= 0 and opp_lives <= 0:
            # Both lost
            self.app.switch_screen("GAME_OVER", won=False)
        elif my_lives <= 0:
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

            # Postconditions: Phase transition should be valid
            assert (
                not self.game.phase_state.in_combat
            ), "Should not be in combat after transition"
            assert (
                self.game.phase_state.in_preparation
            ), "Should be in preparation after transition"
            assert (
                self.game.phase_state.prep_seconds_remaining > 0
            ), f"prep_seconds_remaining must be > 0, not {self.game.phase_state.prep_seconds_remaining}"

            # Clear preview sprites when returning to preparation phase
            for sprite in list(self.game.ui_state.route_preview_sprites):
                sprite.kill()
                if self.game.sim_state.render_manager:
                    self.game.sim_state.render_manager.animation_manager.unregister(
                        sprite
                    )
                    # Also remove from units group if present
                    if sprite in self.game.sim_state.render_manager.units:
                        self.game.sim_state.render_manager.units.remove(sprite)
            self.game.ui_state.route_preview_sprites.clear()
            self.game.ui_state.route_unit_previews.clear()  # Clear the queue data too
            if hasattr(self.game.ui_state, "_last_preview_state"):
                self.game.ui_state._last_preview_state = {}
            # Reset spawned unit tracking for next round
            if hasattr(self.game.sim_state.render_manager, "_spawned_unit_ids"):
                self.game.sim_state.render_manager._spawned_unit_ids.clear()

            # Generate gold from gold mines and play effects
            self._generate_gold_from_mines()

            # Update gold mine states to active
            self._update_gold_mine_states(active=True)

    def _generate_gold_from_mines(self) -> None:
        """Play visual effects for gold mines at the start of preparation phase.

        Note: Gold is actually generated server-side. This only plays the visual effect.
        """
        import random
        import time

        if not self.game:
            return

        gold_mines = self.game.ui_state.local_gold_mines

        for sprite in gold_mines.values():
            # Play gold spawn effect at the mine's position
            if (
                hasattr(self.game.sim_state, "render_manager")
                and self.game.sim_state.render_manager
            ):
                self.game.sim_state.render_manager.sprite_factory.create_effect(
                    sprite.rect.centerx, sprite.rect.centery, "gold_spawn"
                )

            # Show floating gold amount per mine
            gold_amount = random.randint(5, 15)
            self.game.ui_state.floating_mine_gold_texts.append(
                {
                    "amount": gold_amount,
                    "x": sprite.rect.centerx,
                    "y": sprite.rect.top - 10,
                    "start_time": time.time(),
                }
            )

        if gold_mines:
            # Calculate total gold from all mine text
            total_gold_from_mines = reduce(
                lambda acc, text_data: acc + text_data.get("amount", 0),
                self.game.ui_state.floating_mine_gold_texts,
                0,
            )
            logger.info(
                f"Played gold spawn effects for {len(gold_mines)} gold mines (total: {total_gold_from_mines}g)"
            )

    def _update_gold_mine_states(self, active: bool) -> None:
        """Update all gold mines to active or inactive state."""
        if not self.game:
            return

        # Update locally placed gold mines
        for sprite in self.game.ui_state.local_gold_mines.values():
            if hasattr(sprite, "set_active"):
                sprite.set_active(active)

        # Also update simulation-side gold mines (opponent's mines)
        if (
            hasattr(self.game.sim_state, "render_manager")
            and self.game.sim_state.render_manager
        ):
            for sprite in (
                self.game.sim_state.render_manager.sprite_factory.tower_sprites.values()
            ):
                if hasattr(sprite, "set_active"):
                    sprite.set_active(active)

    def _on_tower_placed(self, event: TowerPlacedEvent) -> None:
        """Handle tower placed event from EventBus."""
        # Preconditions
        assert event is not None, "event must not be None"
        assert event.player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{event.player_id}'"
        assert event.tile_row >= 0, f"tile_row must be >= 0, not {event.tile_row}"
        assert event.tile_col >= 0, f"tile_col must be >= 0, not {event.tile_col}"
        assert (
            isinstance(event.tower_type, str) and event.tower_type
        ), "tower_type must be a non-empty string"
        assert event.level >= 1, f"level must be >= 1, not {event.level}"

        if not self.game:
            return

        grid = self.game.get_player_grid(event.player_id)
        if grid.is_buildable(event.tile_row, event.tile_col):
            grid.place_tower(event.tile_row, event.tile_col)

        self.game.sim_state.build_controller.spawn_tower(
            event.player_id, event.tile_row, event.tile_col, event.tower_type
        )
