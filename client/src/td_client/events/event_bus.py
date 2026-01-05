"""Central event bus for publish/subscribe event handling.

The EventBus provides a thread-safe way to:
- Subscribe handlers to specific event types
- Publish events to all interested subscribers
- Handle events synchronously or queue them for later processing

Usage:
    bus = EventBus()

    # Subscribe to events
    bus.subscribe(RoundStartEvent, my_handler)
    bus.subscribe(NetworkEvent, handle_all_network_events)  # Catches all subclasses

    # Publish events
    bus.publish(RoundStartEvent(round_start_pb=data))

    # Process queued events (call this in the main loop)
    bus.process_pending()
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from .events import Event

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Event)


class EventBus:
    """Thread-safe central event dispatcher.

    Events published from background threads are queued and processed
    on the main thread when `process_pending()` is called.
    """

    def __init__(self) -> None:
        # Map from event type to list of handlers
        self._handlers: dict[type[Event], list[Callable[[Event], None]]] = defaultdict(
            list
        )
        # Lock for thread-safe handler registration
        self._lock = threading.Lock()
        # Queue for events published from background threads
        self._pending_events: list[Event] = []
        self._pending_lock = threading.Lock()
        # Track the main thread for direct vs queued dispatch
        self._main_thread_id: int | None = None

    def set_main_thread(self) -> None:
        """Mark the current thread as the main thread for synchronous dispatch."""
        self._main_thread_id = threading.get_ident()

    def subscribe(
        self, event_type: type[T], handler: Callable[[T], None]
    ) -> Callable[[], None]:
        """Subscribe a handler to an event type.

        The handler will be called for events of the specified type AND any subclasses.

        Args:
            event_type: The event class to subscribe to
            handler: Callback function that takes the event as argument

        Returns:
            Unsubscribe function - call it to remove the subscription
        """
        with self._lock:
            self._handlers[event_type].append(handler)  # type: ignore
            logger.debug(
                "Subscribed %s to %s (total: %d)",
                handler.__name__ if hasattr(handler, "__name__") else handler,
                event_type.__name__,
                len(self._handlers[event_type]),
            )

        def unsubscribe() -> None:
            with self._lock:
                try:
                    self._handlers[event_type].remove(handler)  # type: ignore
                except ValueError:
                    pass  # Already removed

        return unsubscribe

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers.

        If called from the main thread, handlers are invoked immediately.
        If called from a background thread, the event is queued for
        processing on the main thread via `process_pending()`.

        Args:
            event: The event to publish
        """
        current_thread = threading.get_ident()

        if self._main_thread_id is None or current_thread == self._main_thread_id:
            # Main thread or not configured - dispatch immediately
            self._dispatch(event)
        else:
            # Background thread - queue for main thread
            with self._pending_lock:
                self._pending_events.append(event)
                logger.debug(
                    "Queued event %s from background thread (pending: %d)",
                    type(event).__name__,
                    len(self._pending_events),
                )

    def process_pending(self) -> int:
        """Process all pending events queued from background threads.

        This should be called once per frame in the main game loop.

        Returns:
            Number of events processed
        """
        # Atomically grab all pending events
        with self._pending_lock:
            if not self._pending_events:
                return 0
            events = self._pending_events.copy()
            self._pending_events.clear()

        # Dispatch each event
        for event in events:
            self._dispatch(event)

        return len(events)

    def _dispatch(self, event: Event) -> None:
        """Dispatch an event to all matching handlers.

        Handlers registered for the event's type AND any parent types
        will be called.
        """
        event_type = type(event)
        handlers_called = 0

        with self._lock:
            # Get handlers for this specific type and all parent types
            for registered_type, handlers in self._handlers.items():
                if isinstance(event, registered_type):
                    for handler in handlers:
                        try:
                            handler(event)
                            handlers_called += 1
                        except Exception:
                            logger.exception(
                                "Error in event handler %s for %s",
                                handler.__name__
                                if hasattr(handler, "__name__")
                                else handler,
                                event_type.__name__,
                            )

        if handlers_called == 0:
            logger.debug("No handlers for event %s", event_type.__name__)
        else:
            logger.debug(
                "Dispatched %s to %d handlers", event_type.__name__, handlers_called
            )

    def clear(self) -> None:
        """Remove all subscriptions and pending events."""
        with self._lock:
            self._handlers.clear()
        with self._pending_lock:
            self._pending_events.clear()

    def has_subscribers(self, event_type: type[Event]) -> bool:
        """Check if there are any subscribers for an event type."""
        with self._lock:
            return bool(self._handlers.get(event_type))
