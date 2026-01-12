from __future__ import annotations

import logging

from td_shared.game import UNIT_STATS, SimUnitData

logger = logging.getLogger(__name__)


class WaveQueue:
    """Queues units for the next wave and assigns spawn ticks deterministically."""

    def __init__(self) -> None:
        self._units_next_wave: list[SimUnitData] = []

    def prepare_units(
        self, player_id: str, units: list[SimUnitData]
    ) -> tuple[int, list[SimUnitData]]:
        """Normalise input units and compute total cost, without mutating state."""
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert units is not None, "units must not be None"
        assert isinstance(units, list), "units must be a list"

        total_cost = 0
        normalized: list[SimUnitData] = []

        for u in units:
            assert isinstance(u, dict), "Each unit must be a dictionary"
            assert "unit_type" in u, "Unit must have 'unit_type' field"
            assert "route" in u, "Unit must have 'route' field"

            unit_type = u["unit_type"]

            if unit_type not in UNIT_STATS:
                logger.warning("Unknown unit_type in SendUnits: %s", unit_type)
                continue

            unit_cost = int(UNIT_STATS[unit_type]["cost"])
            assert unit_cost >= 0, f"Unit cost must not be negative: {unit_cost}"
            total_cost += unit_cost

            route = int(u["route"])
            assert route >= 0, f"route must be >= 0, not {route}"

            spawn_tick = int(u.get("spawn_tick", 0))
            assert spawn_tick >= 0, f"spawn_tick must be >= 0, not {spawn_tick}"

            data: SimUnitData = {
                "player_id": u.get("player_id", player_id),  # type: ignore[arg-type]
                "unit_type": unit_type,
                "route": route,
                "spawn_tick": spawn_tick,
            }

            normalized.append(data)

        # Postcondition
        assert total_cost >= 0, f"total_cost must be >= 0, not {total_cost}"
        assert len(normalized) <= len(
            units
        ), "Normalized units must not exceed input units"
        for norm_unit in normalized:
            assert "player_id" in norm_unit, "Normalized unit must have 'player_id'"
            assert "unit_type" in norm_unit, "Normalized unit must have 'unit_type'"
            assert "route" in norm_unit, "Normalized unit must have 'route'"
            assert "spawn_tick" in norm_unit, "Normalized unit must have 'spawn_tick'"
            assert norm_unit["player_id"] in (
                "A",
                "B",
            ), f"player_id must be 'A' or 'B': {norm_unit['player_id']}"
            assert norm_unit["route"] >= 0, f"route must be >= 0: {norm_unit['route']}"
            assert (
                norm_unit["spawn_tick"] >= 0
            ), f"spawn_tick must be >= 0: {norm_unit['spawn_tick']}"

        return total_cost, normalized

    def enqueue_units(self, units: list[SimUnitData], tick_rate: int) -> None:
        """Append units to the queue, assigning spawn ticks as needed."""
        # Preconditions
        assert units is not None, "units must not be None"
        assert isinstance(units, list), "units must be a list"
        assert tick_rate > 0, f"tick_rate must be > 0, not {tick_rate}"

        if not units:
            return

        old_queue_size = len(self._units_next_wave)

        delay_ticks = max(1, int(0.5 * tick_rate))

        # Determine last spawn tick per route from already queued units
        current_last_by_route: dict[int, int] = {}
        for queued in self._units_next_wave:
            route = int(queued["route"])
            current_last_by_route[route] = max(
                current_last_by_route.get(route, -delay_ticks),
                int(queued["spawn_tick"]),
            )

        # Group new units per route
        by_route: dict[int, list[SimUnitData]] = {}
        for data in units:
            assert isinstance(data, dict), "Each unit must be a dictionary"
            assert "route" in data, "Unit must have 'route' field"
            route = int(data["route"])
            assert route >= 0, f"route must be >= 0: {route}"
            by_route.setdefault(route, []).append(data)

        for route, new_list in by_route.items():
            # Sort new units per route for deterministic assignment
            new_list.sort(key=lambda d: int(d.get("spawn_tick", 0)))
            base = current_last_by_route.get(route, 0)
            next_tick = base + delay_ticks

            for data in new_list:
                if int(data["spawn_tick"]) == 0:
                    data["spawn_tick"] = next_tick
                    next_tick += delay_ticks
                assert (
                    data["spawn_tick"] >= 0
                ), f"spawn_tick must be >= 0: {data['spawn_tick']}"

        self._units_next_wave.extend(units)

        # Postcondition
        assert (
            len(self._units_next_wave) == old_queue_size + len(units)
        ), f"Number of units in queue should be increased by {len(units)}: expected {old_queue_size + len(units)}, got {len(self._units_next_wave)}"
        for unit in units:
            assert unit in self._units_next_wave, "All units should be in the queue"
            assert (
                unit["spawn_tick"] >= 0
            ), f"spawn_tick must be >= 0: {unit['spawn_tick']}"

    def clear(self) -> None:
        self._units_next_wave.clear()

    def get_units(self) -> list[SimUnitData]:
        return [dict(unit) for unit in self._units_next_wave]
