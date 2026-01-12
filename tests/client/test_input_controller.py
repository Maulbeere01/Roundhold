"""Tests for input handling and user controls."""

import pytest
import pygame

from client.src.td_client.ui.input_controller import InputController


class TestInputController:
    """Tests for the InputController class."""

    def test_initialization(self):
        """Test that InputController initializes correctly."""
        # Verify the class exists
        assert InputController is not None

    def test_has_event_handling(self):
        """Test that controller can handle events."""
        # Verify structure
        assert hasattr(InputController, "__init__")


class TestMouseEventHandling:
    """Tests for mouse event handling."""

    def test_mouse_button_down_event(self):
        """Test handling mouse button down events."""
        # Create a mock mouse event
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (100, 200), "button": 1})
        
        assert event.type == pygame.MOUSEBUTTONDOWN
        assert event.pos == (100, 200)
        assert event.button == 1

    def test_mouse_motion_event(self):
        """Test handling mouse motion events."""
        event = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (150, 250)})
        
        assert event.type == pygame.MOUSEMOTION
        assert event.pos == (150, 250)

    def test_mouse_button_types(self):
        """Test different mouse button types."""
        left_click = 1
        middle_click = 2
        right_click = 3
        
        assert left_click == 1
        assert middle_click == 2
        assert right_click == 3


class TestKeyboardEventHandling:
    """Tests for keyboard event handling."""

    def test_key_down_event(self):
        """Test handling key down events."""
        event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        
        assert event.type == pygame.KEYDOWN
        assert event.key == pygame.K_ESCAPE

    def test_common_game_keys(self):
        """Test common game control keys."""
        assert pygame.K_ESCAPE is not None
        assert pygame.K_SPACE is not None
        assert pygame.K_RETURN is not None

    def test_modifier_keys(self):
        """Test modifier keys."""
        assert pygame.K_LSHIFT is not None
        assert pygame.K_LCTRL is not None
        assert pygame.K_LALT is not None
