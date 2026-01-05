"""Tests for the centralized event system."""

import threading

import pytest

from client.src.td_client.events import (
    BuildTowerResponseEvent,
    EventBus,
    GoldChangedEvent,
    HoverTileChangedEvent,
    LivesChangedEvent,
    NetworkEvent,
    OpponentDisconnectedEvent,
    PhaseChangedEvent,
    QueueUpdateEvent,
    RequestBuildTowerEvent,
    RoundChangedEvent,
    RoundResultEvent,
    RoundStartEvent,
    ToggleBuildModeEvent,
    TowerPlacedEvent,
)


class TestEventBus:
    """Tests for the EventBus class."""

    def test_subscribe_and_publish(self):
        """Test basic subscribe and publish functionality."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        bus.subscribe(TowerPlacedEvent, handler)

        event = TowerPlacedEvent(
            player_id="A", tower_type="standard", tile_row=5, tile_col=5
        )
        bus.publish(event)

        assert len(received) == 1
        assert received[0] == event

    def test_unsubscribe(self):
        """Test that unsubscribe removes the handler."""
        bus = EventBus()
        received = []

        def handler(event):
            received.append(event)

        unsubscribe = bus.subscribe(TowerPlacedEvent, handler)

        # First publish should work
        event1 = TowerPlacedEvent(
            player_id="A", tower_type="standard", tile_row=1, tile_col=1
        )
        bus.publish(event1)
        assert len(received) == 1

        # Unsubscribe
        unsubscribe()

        # Second publish should not reach handler
        event2 = TowerPlacedEvent(
            player_id="A", tower_type="standard", tile_row=2, tile_col=2
        )
        bus.publish(event2)
        assert len(received) == 1  # Still only 1

    def test_multiple_handlers(self):
        """Test multiple handlers for the same event type."""
        bus = EventBus()
        received1 = []
        received2 = []

        bus.subscribe(RoundStartEvent, lambda e: received1.append(e))
        bus.subscribe(RoundStartEvent, lambda e: received2.append(e))

        event = RoundStartEvent(round_start_pb=None)
        bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_inheritance_subscription(self):
        """Test that subscribing to parent class receives child events."""
        bus = EventBus()
        received = []

        # Subscribe to the parent class NetworkEvent
        bus.subscribe(NetworkEvent, lambda e: received.append(e))

        # Publish child events
        bus.publish(
            TowerPlacedEvent(
                player_id="A", tower_type="standard", tile_row=1, tile_col=1
            )
        )
        bus.publish(OpponentDisconnectedEvent())
        bus.publish(QueueUpdateEvent(message="Waiting..."))

        assert len(received) == 3

    def test_event_immutability(self):
        """Test that events are immutable (frozen dataclasses)."""
        event = TowerPlacedEvent(
            player_id="A", tower_type="standard", tile_row=5, tile_col=5
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.player_id = "B"

    def test_background_thread_queuing(self):
        """Test that events from background threads are queued."""
        bus = EventBus()
        bus.set_main_thread()
        received = []

        bus.subscribe(RoundStartEvent, lambda e: received.append(e))

        # Publish from background thread
        def background_publish():
            bus.publish(RoundStartEvent(round_start_pb=None))

        thread = threading.Thread(target=background_publish)
        thread.start()
        thread.join()

        # Event should not be dispatched yet
        assert len(received) == 0

        # Process pending events
        count = bus.process_pending()
        assert count == 1
        assert len(received) == 1

    def test_main_thread_immediate_dispatch(self):
        """Test that events from main thread are dispatched immediately."""
        bus = EventBus()
        bus.set_main_thread()
        received = []

        bus.subscribe(RoundStartEvent, lambda e: received.append(e))
        bus.publish(RoundStartEvent(round_start_pb=None))

        # Should be received immediately without process_pending
        assert len(received) == 1

    def test_clear(self):
        """Test clearing all subscriptions and pending events."""
        bus = EventBus()
        received = []

        bus.subscribe(RoundStartEvent, lambda e: received.append(e))
        bus.clear()

        bus.publish(RoundStartEvent(round_start_pb=None))
        assert len(received) == 0


class TestEventTypes:
    """Tests for specific event types."""

    def test_tower_placed_event(self):
        """Test TowerPlacedEvent creation and attributes."""
        event = TowerPlacedEvent(
            player_id="B",
            tower_type="archer",
            tile_row=10,
            tile_col=20,
            level=2,
        )
        assert event.player_id == "B"
        assert event.tower_type == "archer"
        assert event.tile_row == 10
        assert event.tile_col == 20
        assert event.level == 2

    def test_round_result_event(self):
        """Test RoundResultEvent creation."""
        event = RoundResultEvent(
            lives_lost_player_A=2,
            gold_earned_player_A=50,
            lives_lost_player_B=1,
            gold_earned_player_B=30,
            total_lives_player_A=18,
            total_gold_player_A=150,
            total_lives_player_B=19,
            total_gold_player_B=130,
        )
        assert event.lives_lost_player_A == 2
        assert event.total_lives_player_A == 18

    def test_request_build_tower_event(self):
        """Test RequestBuildTowerEvent creation."""
        event = RequestBuildTowerEvent(
            player_id="A",
            tower_type="standard",
            tile_row=5,
            tile_col=5,
            was_empty=True,
            sprite_existed=False,
        )
        assert event.was_empty is True
        assert event.sprite_existed is False

    def test_build_tower_response_event(self):
        """Test BuildTowerResponseEvent creation."""
        event = BuildTowerResponseEvent(
            success=True,
            tile_row=5,
            tile_col=5,
            was_empty=True,
            sprite_existed=False,
        )
        assert event.success is True

    def test_ui_events(self):
        """Test UI event types."""
        toggle = ToggleBuildModeEvent(enabled=True)
        assert toggle.enabled is True

        hover = HoverTileChangedEvent(tile=(5, 10))
        assert hover.tile == (5, 10)

        hover_none = HoverTileChangedEvent(tile=None)
        assert hover_none.tile is None

    def test_state_events(self):
        """Test state change event types."""
        gold = GoldChangedEvent(player_id="A", new_gold=150, delta=50)
        assert gold.new_gold == 150
        assert gold.delta == 50

        lives = LivesChangedEvent(player_id="B", new_lives=18, delta=-2)
        assert lives.new_lives == 18

        phase = PhaseChangedEvent(phase="combat", seconds_remaining=30.0)
        assert phase.phase == "combat"

        round_event = RoundChangedEvent(round_number=5)
        assert round_event.round_number == 5
