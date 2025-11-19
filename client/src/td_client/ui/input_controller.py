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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_g:
                self.debug_renderer.toggle_grid()
            elif event.key == pygame.K_ESCAPE:
                # Cancel tower build mode
                if game.ui_state.tower_build_mode:
                    game.ui_state.tower_build_mode = False
                    game.ui_state.hover_tile = None
                    logger.info("Tower build mode cancelled")
        elif event.type == pygame.MOUSEMOTION:
            if game.ui_state.tower_build_mode:
                self.build_controller.handle_mouse_motion(event, game)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.build_controller.handle_mouse_click(event, game)
