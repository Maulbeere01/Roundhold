from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .base import Screen

if TYPE_CHECKING:
    from ..main import GameApp


class WaitingScreen(Screen):
    """Shown while matchmaking is in progress."""

    def __init__(self, app: GameApp) -> None:
        super().__init__(app)
        self.message: str = "Connecting..."

    def enter(self, **kwargs) -> None:
        self.message = kwargs.get("message", "Searching for opponent...")

    def set_message(self, message: str) -> None:
        self.message = message

    def handle_event(self, event: pygame.event.Event) -> None:
        # No interaction needed in waiting screen
        return None

    def update(self, dt: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        font = pygame.font.Font(None, 32)
        text = font.render(self.message, True, (220, 220, 220))
        w = self.app.display_manager.screen_width
        h = self.app.display_manager.screen_height
        surface.blit(
            text,
            (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2),
        )
