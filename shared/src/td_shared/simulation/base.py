"""Shared base utilities for deterministic simulation entities."""

from __future__ import annotations

import math

from ..game.protocol import PlayerID


def calculate_sim_dt(tick_rate: int) -> float:
    """Default simulation tick rate helper."""
    # Preconditions
    assert isinstance(
        tick_rate, int
    ), f"tick_rate must be an int, not {type(tick_rate)}"
    assert tick_rate > 0, f"tick_rate must be > 0, not {tick_rate}"

    result = 1.0 / float(tick_rate)

    # Postconditions
    assert isinstance(result, float), "Result must be a float"
    assert result > 0, f"Result must be > 0, not {result}"
    assert (
        result == 1.0 / float(tick_rate)
    ), f"Result must equal 1.0 / tick_rate: expected {1.0 / float(tick_rate)}, got {result}"

    return result


class SimEntity:
    """Base class for simulation entities."""

    def __init__(self, entity_id: int, player_id: PlayerID, x: float, y: float):
        """Initialize entity."""
        # Preconditions
        assert isinstance(
            entity_id, int
        ), f"entity_id must be an int, not {type(entity_id)}"
        assert entity_id >= 0, f"entity_id must be >= 0, not {entity_id}"
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert isinstance(x, (int, float)), "x must be numeric"
        assert isinstance(y, (int, float)), "y must be numeric"

        self.entity_id = entity_id
        self.player_id = player_id
        self.x = x
        self.y = y
        self.is_active = True

        # Postconditions
        assert self.entity_id == entity_id, "entity_id must be set correctly"
        assert self.player_id == player_id, "player_id must be set correctly"
        assert self.x == float(x), "x must be set correctly"
        assert self.y == float(y), "y must be set correctly"
        assert self.is_active is True, "is_active must be True after initialization"

    def distance_to(self, other_x: float, other_y: float) -> float:
        """Distance to a point in pixels."""
        # Preconditions
        assert isinstance(other_x, (int, float)), "other_x must be numeric"
        assert isinstance(other_y, (int, float)), "other_y must be numeric"
        assert isinstance(self.x, (int, float)), "self.x must be numeric"
        assert isinstance(self.y, (int, float)), "self.y must be numeric"

        dx = other_x - self.x
        dy = other_y - self.y
        result = math.sqrt(dx * dx + dy * dy)

        # Postconditions
        assert isinstance(result, float), "Result must be a float"
        assert result >= 0, f"Distance must be >= 0, not {result}"
        assert not math.isnan(result), "Distance must not be NaN"
        assert not math.isinf(result), "Distance must not be infinite"

        return result
