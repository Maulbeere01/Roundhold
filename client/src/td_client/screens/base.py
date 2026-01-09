from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..main import GameApp


class Screen:
    """Base class for all UI screens (menu, waiting, game, victory).

    Screens can subscribe to events from the EventBus. Subscriptions are
    automatically managed when entering/leaving screens.
    """

    def __init__(self, app: GameApp) -> None:
        self.app = app
        self._event_subscriptions: list[Callable[[], None]] = []

    def _subscribe_events(self) -> None:
        """Override to subscribe to EventBus events when screen becomes active.

        Use self._add_subscription() to register subscriptions that will be
        automatically cleaned up when the screen is exited.
        """
        pass

    def _add_subscription(self, unsubscribe: Callable[[], None]) -> None:
        """Register an unsubscribe function to be called on screen exit."""
        self._event_subscriptions.append(unsubscribe)

    def _unsubscribe_all(self) -> None:
        """Unsubscribe from all events (called automatically on exit)."""
        for unsub in self._event_subscriptions:
            unsub()
        self._event_subscriptions.clear()

    def enter(self, **kwargs) -> None:
        """Called when the screen becomes active."""
        self._subscribe_events()

    def exit(self) -> None:
        """Called when leaving this screen for another."""
        self._unsubscribe_all()

    def handle_event(self, event: pygame.event.Event) -> None:
        return None

    def update(self, dt: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        return None
