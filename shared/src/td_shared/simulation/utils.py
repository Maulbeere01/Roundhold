"""Shared utilities for deterministic simulation."""

from __future__ import annotations


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
