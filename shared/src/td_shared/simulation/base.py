"""Shared base utilities for deterministic simulation entities."""

from __future__ import annotations

import math

from ..game.protocol import PlayerID


def calculate_sim_dt(tick_rate: int) -> float:
    """Default simulation tick rate helper."""
    return 1.0 / float(tick_rate)


class SimEntity:
    """Base class for simulation entities."""

    def __init__(self, entity_id: int, player_id: PlayerID, x: float, y: float):
        """Initialize entity."""
        self.entity_id = entity_id
        self.player_id = player_id
        self.x = x
        self.y = y
        self.is_active = True

    def distance_to(self, other_x: float, other_y: float) -> float:
        """Distance to a point in pixels."""
        dx = other_x - self.x
        dy = other_y - self.y
        return math.sqrt(dx * dx + dy * dy)
