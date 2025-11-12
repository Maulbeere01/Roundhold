from __future__ import annotations

from td_shared.game import SimulationData


class SnapshotBuilder:
    """Builds SimulationData snapshots from tower placements and wave queue."""

    def __init__(self, placement_service, wave_queue) -> None:
        self.placement_service = placement_service
        self.wave_queue = wave_queue

    def build(self, tick_rate: int) -> SimulationData:
        towers = self.placement_service.get_sim_towers()
        units = self.wave_queue.get_units()
        return SimulationData(
            towers=towers,
            units=units,
            tick_rate=int(tick_rate),
        )

