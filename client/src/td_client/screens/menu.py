from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

from .base import Screen

if TYPE_CHECKING:
    from ..main import GameApp

logger = logging.getLogger(__name__)


class MenuScreen(Screen):
    """Main menu with 'Find Match' button."""

    def __init__(self, app: GameApp) -> None:
        super().__init__(app)
        w = app.display_manager.screen_width
        h = app.display_manager.screen_height
        self.button_rect = pygame.Rect(w // 2 - 120, h // 2 - 30, 240, 60)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                logger.info("User clicked Find Match, queuing...")
                self.app.network_client.queue_for_match(
                    player_name="Player",
                    on_match_found=self.app.router.on_match_found,
                    on_queue_update=self.app.router.on_queue_update,
                    on_round_start=self.app.router.on_round_start,
                    on_round_result=self.app.router.on_round_result,
                    on_tower_placed=self.app.router.on_tower_placed,
                    on_opponent_disconnected=self.app.router.on_opponent_disconnected,
                )
                self.app.switch_screen("WAITING")

    def update(self, dt: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (60, 120, 200), self.button_rect, border_radius=8)
        font = pygame.font.Font(None, 36)
        text = font.render("Find Match", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.button_rect.center)
        surface.blit(text, text_rect)
