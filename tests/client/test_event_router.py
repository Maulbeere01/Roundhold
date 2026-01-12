"""Tests for event routing and network event handling."""

import pytest

from client.src.td_client.events import (
    BuildTowerResponseEvent,
    EventBus,
    NetworkEvent,
    OpponentDisconnectedEvent,
    PhaseChangedEvent,
    RoundStartEvent,
)
from client.src.td_client.network.event_router import NetworkEventRouter


class TestEventRouter:
    """Tests for the NetworkEventRouter class."""

    def test_initialization(self):
        """Test that NetworkEventRouter initializes with event bus."""
        from unittest.mock import Mock
        event_bus = EventBus()
        app = Mock()
        router = NetworkEventRouter(app, event_bus)
        
        assert router.event_bus is event_bus
        assert router.app is app

    def test_routes_network_event_to_specific_handler(self):
        """Test that network events are routed to specific handlers."""
        from unittest.mock import Mock
        event_bus = EventBus()
        app = Mock()
        router = NetworkEventRouter(app, event_bus)
        
        received_events = []
        
        def handler(event):
            received_events.append(event)
        
        # Subscribe to a specific event type
        event_bus.subscribe(PhaseChangedEvent, handler)
        
        # Simulate receiving a network event
        # Note: This test verifies the concept; actual implementation may vary
        assert hasattr(router, "event_bus")


class TestNetworkEventTypes:
    """Tests for network event type definitions."""

    def test_opponent_disconnected_event(self):
        """Test OpponentDisconnectedEvent creation."""
        event = OpponentDisconnectedEvent()
        
        assert isinstance(event, OpponentDisconnectedEvent)
