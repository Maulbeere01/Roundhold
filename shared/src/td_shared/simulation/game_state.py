from __future__ import annotations

from ..game.protocol import PlayerID, SimulationData
from .base import calculate_sim_dt
from .entities import SimTower, SimUnit


class GameState:
    """Deterministic single-round simulation state."""

    def __init__(self, simulation_data: SimulationData):
        self.tick_rate = simulation_data["tick_rate"]
        self.sim_dt = calculate_sim_dt(self.tick_rate)
        self.current_tick = 0

        # Kill counters for reward distribution
        self.kills_by_player_A = 0
        self.kills_by_player_B = 0

        # Lives lost tracking (units reaching enemy base)
        self.lives_lost_player_A = 0
        self.lives_lost_player_B = 0

        # Timed end-condition controls
        self.min_duration_ticks = 5 * self.tick_rate
        self.post_combat_delay_ticks = 3 * self.tick_rate
        self.last_unit_inactive_tick: int | None = None

        # Create towers
        self.towers: list[SimTower] = []
        for tower_id, tower_data in enumerate(simulation_data["towers"]):
            tower = SimTower(
                entity_id=tower_id,
                player_id=tower_data["player_id"],
                tower_type=tower_data["tower_type"],
                x=tower_data["position_x"],
                y=tower_data["position_y"],
                level=tower_data["level"],
            )
            self.towers.append(tower)

        # Create units (will spawn based on spawn_tick)
        self.units: list[SimUnit] = []
        for unit_id, unit_data in enumerate(simulation_data["units"]):
            unit = SimUnit(
                entity_id=unit_id,
                player_id=unit_data["player_id"],
                unit_type=unit_data["unit_type"],
                route=unit_data["route"],
                sim_dt=self.sim_dt,
            )

            # Units start inactive until spawn_tick
            unit.is_active = False
            self.units.append(unit)

        # Track spawn ticks
        self._unit_spawn_ticks = {
            unit.entity_id: unit_data["spawn_tick"]
            for unit, unit_data in zip(
                self.units, simulation_data["units"], strict=False
            )
        }

        # Track units that have not spawned yet
        self._pending_units = set(self._unit_spawn_ticks.keys())

        # Active units list (updated each tick)
        self.active_units: list[SimUnit] = []

    def update_tick(self) -> None:
        """Advance simulation by one tick."""

        # Spawn units that should spawn this tick
        for unit in self.units:
            if not unit.is_active:
                spawn_tick = self._unit_spawn_ticks[unit.entity_id]
                if (
                    unit.entity_id in self._pending_units
                    and self.current_tick >= spawn_tick
                ):
                    unit.is_active = True
                    self._pending_units.discard(unit.entity_id)

        # Update active units list
        self.active_units = [u for u in self.units if u.is_active]

        # Update all active units (movement)
        for unit in self.active_units:
            unit.update()

        # Update towers (targeting and shooting)
        for tower in self.towers:
            if tower.is_active:
                tower.update(self.active_units, self)

        # Check for units that reached base and count lives lost
        for unit in self.active_units:
            if unit.has_reached_base():
                if unit.player_id == "A":
                    self.lives_lost_player_B += unit.base_damage
                else:
                    self.lives_lost_player_A += unit.base_damage

        # Remove units that reached base or died
        self.active_units = [u for u in self.active_units if u.is_active]
        # If all units are inactive and none pending, record first completion tick
        # Only set this after minimum duration has passed to ensure simulation runs for at least min_duration_ticks
        if (
            len(self.active_units) == 0
            and len(self._pending_units) == 0
            and self.last_unit_inactive_tick is None
            and self.current_tick >= self.min_duration_ticks
        ):
            self.last_unit_inactive_tick = self.current_tick

        # Increment tick counter
        self.current_tick += 1

    def get_units_reached_base(self, player_id: PlayerID) -> int:
        """Number of enemy units that reached this player's base."""
        count = 0
        for unit in self.units:
            if unit.has_reached_base() and unit.player_id != player_id:
                count += 1
        return count

    def is_simulation_complete(self) -> bool:
        """Check if simulation is complete using timed end condition."""
        min_duration_passed = self.current_tick >= self.min_duration_ticks
        if self.last_unit_inactive_tick is not None:
            ticks_since_end = self.current_tick - self.last_unit_inactive_tick
            delay_passed = ticks_since_end >= self.post_combat_delay_ticks
            return bool(min_duration_passed and delay_passed)
        return False

    def get_kills_by_player(self, player_id: PlayerID) -> int:
        if player_id == "A":
            return self.kills_by_player_A
        return self.kills_by_player_B
