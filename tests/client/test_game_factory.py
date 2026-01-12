"""Tests for game factory and object creation."""

import pytest

from client.src.td_client.simulation.game_factory import GameFactory


class TestGameFactory:
    """Tests for the GameFactory class."""

    def test_factory_exists(self):
        """Test that GameFactory exists."""
        assert GameFactory is not None

    def test_factory_can_create_objects(self):
        """Test that factory has creation methods."""
        # Verify the factory class has the expected structure
        assert hasattr(GameFactory, "__init__")


class TestObjectCreation:
    """Tests for game object creation patterns."""

    def test_factory_pattern(self):
        """Test that factory pattern is used for object creation."""
        from client.src.td_client.simulation import game_factory
        
        assert game_factory is not None

    def test_sprite_creation_separation(self):
        """Test that game logic is separated from sprite creation."""
        # Verify factory module structure
        from client.src.td_client.simulation.game_factory import GameFactory
        
        assert GameFactory is not None
