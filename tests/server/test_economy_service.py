"""Tests for economy and gold management."""

import pytest

from server.src.td_server.services.economy import EconomyManager
from td_shared.game import GOLD_PER_KILL, START_GOLD, PLAYER_LIVES


class TestEconomyService:
    """Tests for the EconomyManager class."""

    def test_initialization_default_gold(self):
        """Test that service initializes with default starting gold."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        # Both players should start with default gold
        gold_a = service.get_gold("A")
        gold_b = service.get_gold("B")
        
        assert gold_a == START_GOLD
        assert gold_b == START_GOLD

    def test_get_gold_invalid_player(self):
        """Test getting gold for invalid player returns 0 or raises error."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        # Implementation may vary - either returns 0 or raises error
        try:
            gold = service.get_gold("X")  # type: ignore
            assert gold == 0
        except (KeyError, ValueError):
            pass  # Acceptable to raise error

    def test_spend_gold_success(self):
        """Test successful gold spending."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        initial_gold = service.get_gold("A")
        
        result = service.spend_gold("A", 50)
        
        assert result is True
        assert service.get_gold("A") == initial_gold - 50

    def test_spend_gold_insufficient_funds(self):
        """Test that spending more gold than available fails."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        result = service.spend_gold("A", 99999)
        
        assert result is False
        assert service.get_gold("A") == START_GOLD  # Unchanged

    def test_spend_gold_exact_amount(self):
        """Test spending exact amount of gold available."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        current_gold = service.get_gold("A")
        
        result = service.spend_gold("A", current_gold)
        
        assert result is True
        assert service.get_gold("A") == 0

    def test_add_gold(self):
        """Test adding gold to player."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        initial_gold = service.get_gold("A")
        
        service.add_gold("A", 100)
        
        assert service.get_gold("A") == initial_gold + 100

    def test_add_gold_for_kills(self):
        """Test adding gold based on kill count."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        initial_gold = service.get_gold("A")
        
        kills = 10
        gold_earned = kills * GOLD_PER_KILL
        service.add_gold("A", gold_earned)
        
        assert service.get_gold("A") == initial_gold + gold_earned

    def test_negative_gold_prevention(self):
        """Test that gold cannot go negative."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        # Try to spend more than available
        service.spend_gold("A", 99999)
        
        # Gold should never be negative
        assert service.get_gold("A") >= 0

    def test_multiple_transactions(self):
        """Test multiple gold transactions."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        service.spend_gold("A", 100)
        service.add_gold("A", 50)
        service.spend_gold("A", 25)
        
        expected = START_GOLD - 100 + 50 - 25
        assert service.get_gold("A") == expected

    def test_independent_player_gold(self):
        """Test that player gold is independent."""
        service = EconomyManager(PLAYER_LIVES, START_GOLD)
        
        service.spend_gold("A", 100)
        service.add_gold("B", 200)
        
        assert service.get_gold("A") == START_GOLD - 100
        assert service.get_gold("B") == START_GOLD + 200
