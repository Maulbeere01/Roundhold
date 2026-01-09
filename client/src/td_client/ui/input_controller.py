from __future__ import annotations

import logging

import pygame

logger = logging.getLogger(__name__)


class InputController:
    """Routes input events to the appropriate handlers."""

    def __init__(self, build_controller, debug_renderer) -> None:
        self.build_controller = build_controller
        self.debug_renderer = debug_renderer

    def handle_event(self, event, game) -> None:
        # Preconditions
        assert event is not None, "event must not be None"
        assert game is not None, "game must not be None"

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.debug_renderer.toggle_grid()

            # Unit selection keys
            elif event.key == pygame.K_1:
                game.ui_state.selected_unit_type = "standard"
                logger.info("Selected unit: Warrior (Key 1)")
            elif event.key == pygame.K_2:
                game.ui_state.selected_unit_type = "pawn"
                logger.info("Selected unit: Pawn (Key 2)")
            elif event.key == pygame.K_3:
                game.ui_state.selected_unit_type = "archer"
                logger.info("Selected unit: Archer (Key 3)")

            elif event.key == pygame.K_ESCAPE:
                # Cancel tower build mode
                if game.ui_state.tower_build_mode:
                    game.ui_state.tower_build_mode = False
                    game.ui_state.hover_tile = None
                    logger.info("Tower build mode cancelled")
                    # Postcondition: Build mode should be cancelled
                    assert (
                        not game.ui_state.tower_build_mode
                    ), "tower_build_mode should be False after cancellation"
                    assert (
                        game.ui_state.hover_tile is None
                    ), "hover_tile should be None after cancellation"
        elif event.type == pygame.MOUSEMOTION:
            # Always handle mouse motion for route button hover detection
            self.build_controller.handle_mouse_motion(event, game)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Precondition: Left mouse button click
            assert (
                event.button == 1
            ), f"Expected left mouse button (1), got {event.button}"
            self.build_controller.handle_mouse_click(event, game)
