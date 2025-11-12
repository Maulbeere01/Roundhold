from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from td_shared.game import SimUnitData, UNIT_STATS

logger = logging.getLogger(__name__)


class WaveQueue:
    """Queues units for the next wave and assigns spawn ticks deterministically."""

    def __init__(self) -> None:
        self._units_next_wave: List[SimUnitData] = []

    def prepare_units(self, player_id: str, units: List[SimUnitData]) -> Tuple[int, List[SimUnitData]]:
        """Normalise input units and compute total cost, without mutating state."""
        total_cost = 0
        normalized: List[SimUnitData] = []
        for u in units:
            unit_type = u["unit_type"]
            if unit_type not in UNIT_STATS:
                logger.warning("Unknown unit_type in SendUnits: %s", unit_type)
                continue
            total_cost += int(UNIT_STATS[unit_type]["cost"])
            data: SimUnitData = {
                "player_id": u.get("player_id", player_id),  # type: ignore[arg-type]
                "unit_type": unit_type,
                "route": int(u["route"]),
                "spawn_tick": int(u.get("spawn_tick", 0)),
            }
            normalized.append(data)
        return total_cost, normalized

    def enqueue_units(self, units: List[SimUnitData], tick_rate: int) -> None:
        """Append units to the queue, assigning spawn ticks as needed."""
        if not units:
            return
        delay_ticks = max(1, int(0.5 * tick_rate))

        # Determine last spawn tick per route from already queued units
        current_last_by_route: Dict[int, int] = {}
        for queued in self._units_next_wave:
            route = int(queued["route"])
            current_last_by_route[route] = max(current_last_by_route.get(route, -delay_ticks), int(queued["spawn_tick"]))

        # Group new units per route
        by_route: Dict[int, List[SimUnitData]] = {}
        for data in units:
            route = int(data["route"])
            by_route.setdefault(route, []).append(data)

        for route, new_list in by_route.items():
            # Sort new units per route for deterministic assignment
            new_list.sort(key=lambda d: int(d.get("spawn_tick", 0)))
            base = current_last_by_route.get(route, -delay_ticks)
            next_tick = base + delay_ticks
            for data in new_list:
                if int(data["spawn_tick"]) <= 0:
                    data["spawn_tick"] = next_tick
                    next_tick += delay_ticks

        self._units_next_wave.extend(units)

    def clear(self) -> None:
        self._units_next_wave.clear()

    def get_units(self) -> List[SimUnitData]:
        return [dict(unit) for unit in self._units_next_wave]

