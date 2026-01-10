from __future__ import annotations

from ..game.game_balance import PLAYER_LIVES
from ..game.protocol import PlayerID, SimulationData
from .sim_tower import SimTower
from .sim_unit import SimUnit
from .utils import calculate_sim_dt


class GameState:
    """Deterministic single-round simulation state."""

    def __init__(self, simulation_data: SimulationData):
        # Preconditions
        assert isinstance(simulation_data, dict), "simulation_data must be a dict"
        assert (
            "tick_rate" in simulation_data
        ), "simulation_data must have 'tick_rate' field"
        assert "towers" in simulation_data, "simulation_data must have 'towers' field"
        assert "units" in simulation_data, "simulation_data must have 'units' field"
        assert isinstance(simulation_data["tick_rate"], int), "tick_rate must be an int"
        assert (
            simulation_data["tick_rate"] > 0
        ), f"tick_rate must be > 0, not {simulation_data['tick_rate']}"
        assert isinstance(simulation_data["towers"], list), "towers must be a list"
        assert isinstance(simulation_data["units"], list), "units must be a list"

        self.tick_rate = simulation_data["tick_rate"]
        self.sim_dt = calculate_sim_dt(self.tick_rate)
        self.current_tick = 0

        # Gold earned from kills
        self.gold_earned_by_player_A = 0
        self.gold_earned_by_player_B = 0

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
            assert isinstance(tower_data, dict), "Each tower_data must be a dict"
            assert "player_id" in tower_data, "Tower must have 'player_id' field"
            assert "tower_type" in tower_data, "Tower must have 'tower_type' field"
            assert "position_x" in tower_data, "Tower must have 'position_x' field"
            assert "position_y" in tower_data, "Tower must have 'position_y' field"
            assert "level" in tower_data, "Tower must have 'level' field"
            assert tower_data["player_id"] in (
                "A",
                "B",
            ), f"Tower player_id must be 'A' or 'B', not '{tower_data['player_id']}'"
            assert (
                tower_data["level"] >= 1
            ), f"Tower level must be >= 1, not {tower_data['level']}"
            assert tower_id >= 0, f"tower_id must be >= 0, not {tower_id}"

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

        # Track units per route for offset calculation
        route_unit_counts: dict[tuple[str, int], int] = {}

        for unit_id, unit_data in enumerate(simulation_data["units"]):
            assert isinstance(unit_data, dict), "Each unit_data must be a dict"
            assert "player_id" in unit_data, "Unit must have 'player_id' field"
            assert "unit_type" in unit_data, "Unit must have 'unit_type' field"
            assert "route" in unit_data, "Unit must have 'route' field"
            assert "spawn_tick" in unit_data, "Unit must have 'spawn_tick' field"
            assert unit_data["player_id"] in (
                "A",
                "B",
            ), f"Unit player_id must be 'A' or 'B', not '{unit_data['player_id']}'"
            assert (
                unit_data["route"] >= 1
            ), f"Unit route must be >= 1, not {unit_data['route']}"
            assert (
                unit_data["spawn_tick"] >= 0
            ), f"Unit spawn_tick must be >= 0, not {unit_data['spawn_tick']}"
            assert unit_id >= 0, f"unit_id must be >= 0, not {unit_id}"

            unit = SimUnit(
                entity_id=unit_id,
                player_id=unit_data["player_id"],
                unit_type=unit_data["unit_type"],
                route=unit_data["route"],
                sim_dt=self.sim_dt,
            )

            # Apply spawn offset based on queue position for this route
            route_key = (unit_data["player_id"], unit_data["route"])
            idx = route_unit_counts.get(route_key, 0)
            route_unit_counts[route_key] = idx + 1

            # Calculate offset - spread in grid pattern matching preview
            col_idx = idx % 3
            row_idx = idx // 3
            unit.spawn_offset_x = (col_idx - 1) * 20.0
            unit.spawn_offset_y = -row_idx * 24.0 - 30.0
            unit.ease_progress = 0.0  # Start easing in

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

        # Postconditions
        assert (
            self.tick_rate > 0
        ), f"tick_rate must be > 0 after initialization: {self.tick_rate}"
        assert (
            self.sim_dt > 0
        ), f"sim_dt must be > 0 after initialization: {self.sim_dt}"
        assert self.current_tick == 0, "current_tick must be 0 after initialization"
        assert (
            self.gold_earned_by_player_A == 0
        ), "gold_earned_by_player_A must be 0 after initialization"
        assert (
            self.gold_earned_by_player_B == 0
        ), "gold_earned_by_player_B must be 0 after initialization"
        assert (
            self.lives_lost_player_A == 0
        ), "lives_lost_player_A must be 0 after initialization"
        assert (
            self.lives_lost_player_B == 0
        ), "lives_lost_player_B must be 0 after initialization"
        assert len(self.towers) == len(
            simulation_data["towers"]
        ), "Tower count must match input"
        assert len(self.units) == len(
            simulation_data["units"]
        ), "Unit count must match input"
        assert len(self._unit_spawn_ticks) == len(
            self.units
        ), "Spawn ticks count must match units count"
        assert len(self._pending_units) == len(
            self.units
        ), "Pending units count must match units count"

    def update_tick(self) -> None:
        """Advance simulation by one tick."""
        # Preconditions
        assert (
            self.current_tick >= 0
        ), f"current_tick must be >= 0, not {self.current_tick}"
        assert (
            self.lives_lost_player_A >= 0
        ), f"lives_lost_player_A must be >= 0, not {self.lives_lost_player_A}"
        assert (
            self.lives_lost_player_B >= 0
        ), f"lives_lost_player_B must be >= 0, not {self.lives_lost_player_B}"
        assert (
            self.gold_earned_by_player_A >= 0
        ), f"gold_earned_by_player_A must be >= 0, not {self.gold_earned_by_player_A}"
        assert (
            self.gold_earned_by_player_B >= 0
        ), f"gold_earned_by_player_B must be >= 0, not {self.gold_earned_by_player_B}"

        old_tick = self.current_tick

        # Spawn units that should spawn this tick
        for unit in self.units:
            if not unit.is_active:
                assert (
                    unit.entity_id in self._unit_spawn_ticks
                ), f"Unit {unit.entity_id} must have spawn_tick"
                spawn_tick = self._unit_spawn_ticks[unit.entity_id]
                assert spawn_tick >= 0, f"spawn_tick must be >= 0, not {spawn_tick}"
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

        # Deactivate a player's towers once their lives are depleted (castle destroyed)
        if self.lives_lost_player_A >= PLAYER_LIVES:
            for tower in self.towers:
                if tower.player_id == "A":
                    tower.is_active = False
                    tower.last_shot_target = None
        if self.lives_lost_player_B >= PLAYER_LIVES:
            for tower in self.towers:
                if tower.player_id == "B":
                    tower.is_active = False
                    tower.last_shot_target = None

        # Check for units that reached base and count lives lost
        for unit in self.active_units:
            if unit.has_reached_base():
                assert (
                    unit.base_damage >= 0
                ), f"base_damage must be >= 0, not {unit.base_damage}"
                if unit.player_id == "A":
                    old_lives_B = self.lives_lost_player_B
                    self.lives_lost_player_B += unit.base_damage
                    assert (
                        self.lives_lost_player_B == old_lives_B + unit.base_damage
                    ), "Lives lost not correctly incremented"
                else:
                    old_lives_A = self.lives_lost_player_A
                    self.lives_lost_player_A += unit.base_damage
                    assert (
                        self.lives_lost_player_A == old_lives_A + unit.base_damage
                    ), "Lives lost not correctly incremented"

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

        # Postconditions
        assert (
            self.current_tick == old_tick + 1
        ), f"current_tick must be incremented by 1: expected {old_tick + 1}, got {self.current_tick}"
        assert (
            self.lives_lost_player_A >= 0
        ), f"lives_lost_player_A must be >= 0 after update: {self.lives_lost_player_A}"
        assert (
            self.lives_lost_player_B >= 0
        ), f"lives_lost_player_B must be >= 0 after update: {self.lives_lost_player_B}"
        assert (
            self.gold_earned_by_player_A >= 0
        ), f"gold_earned_by_player_A must be >= 0 after update: {self.gold_earned_by_player_A}"
        assert (
            self.gold_earned_by_player_B >= 0
        ), f"gold_earned_by_player_B must be >= 0 after update: {self.gold_earned_by_player_B}"
        assert all(
            u.is_active for u in self.active_units
        ), "All active_units must be active"

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

    def get_gold_earned_by_player(self, player_id: PlayerID) -> int:
        """Get total gold earned from kills by a player."""
        # Preconditions
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"

        if player_id == "A":
            result = self.gold_earned_by_player_A
        else:
            result = self.gold_earned_by_player_B

        # Postcondition
        assert result >= 0, f"Gold earned must be >= 0, not {result}"
        return result
