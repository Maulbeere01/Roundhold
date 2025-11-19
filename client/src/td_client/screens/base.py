from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..main import GameApp


class Screen:
    """Base class for all UI screens (menu, waiting, game, victory)."""

    def __init__(self, app: GameApp) -> None:
        self.app = app

    def enter(self, **kwargs) -> None:
        """Called when the screen becomes active."""
        return None

    def handle_event(self, event: pygame.event.Event) -> None:
        return None

    def update(self, dt: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        return None
