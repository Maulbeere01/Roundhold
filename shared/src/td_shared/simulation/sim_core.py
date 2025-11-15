"""Deterministic simulation core.

all deterministic simulation logic that runs identically on both server and client.
This module must NEVER importPygame or any rendering code, it is pure,
platform-independent game logic.

The simulation uses fixed timesteps (SIM_DT) and deterministic rules to ensure
that server and client produce identical results.
"""

import math

from ..game.game_balance import (
    GAME_PATHS,
    TILE_SIZE_PX,
    TOWER_STATS,
    UNIT_STATS,
    tile_to_pixel,
)
from ..game.protocol import PlayerID, SimulationData


# Default simulation tick rate (can be overridden by SimulationData) set in game_balance.py
def calculate_sim_dt(tick_rate: int) -> float:
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


class SimUnit(SimEntity):
    """Attacking unit following a predefined path."""

    def __init__(
        self,
        entity_id: int,
        player_id: PlayerID,
        unit_type: str,
        route: int,
        sim_dt: float,
    ):
        """Initialize unit."""
        # Get unit stats
        if unit_type not in UNIT_STATS:
            raise ValueError(f"Unknown unit type: {unit_type}")
        stats = UNIT_STATS[unit_type]

        # Get path for this route
        if player_id not in GAME_PATHS:
            raise ValueError(f"Unknown player_id: {player_id}")
        if route not in GAME_PATHS[player_id]:
            raise ValueError(f"Unknown route: {route}")

        path_tiles = GAME_PATHS[player_id][route]

        # Convert to pixel coordinates in local simulation space
        path_pixels = [
            (
                tile_to_pixel(row, col)[0] + TILE_SIZE_PX / 2.0,
                tile_to_pixel(row, col)[1] + TILE_SIZE_PX / 2.0,
            )
            for row, col in path_tiles
        ]

        # Start at first waypoint
        start_x, start_y = path_pixels[0]

        super().__init__(entity_id, player_id, start_x, start_y)

        self.unit_type = unit_type
        self.route = route
        self.max_health = stats["health"]
        self.health = self.max_health
        self.speed = stats["speed"]
        self.path = path_pixels
        self.current_path_index = 0
        self.sim_dt = sim_dt
        self._reached_base = False

    def take_damage(
        self, damage: int, attacker_player_id: PlayerID, game_state: "GameState"
    ) -> None:
        """Apply damage and record kill attribution on death."""
        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.is_active = False
            # count kills for gold distribution
            if attacker_player_id == "A":
                game_state.kills_by_player_A += 1
            else:
                game_state.kills_by_player_B += 1

    def update(self) -> None:
        """Update unit position (deterministic movement along path)."""
        if not self.is_active:
            return

        # Calculate how far the unit can move this TICK
        # speed is in pixels per second, sim_dt is the time step in seconds
        remaining_move_dist = self.speed * self.sim_dt

        while remaining_move_dist > 0:
            # we have reached the base?
            if self.current_path_index >= len(self.path) - 1:
                self._reached_base = True
                self.is_active = False
                return

            next_waypoint = self.path[self.current_path_index + 1]

            dx = next_waypoint[0] - self.x
            dy = next_waypoint[1] - self.y
            distance_to_next = math.sqrt(dx * dx + dy * dy)

            # Case 1: Can reach the next waypoint completely this tick
            if remaining_move_dist >= distance_to_next:
                self.x = next_waypoint[0]
                self.y = next_waypoint[1]
                self.current_path_index += 1
                remaining_move_dist -= distance_to_next
            else:
                # Case 2: Can only move partway to next waypoint
                # Calculate normalized direction vector
                dir_x = dx / distance_to_next
                dir_y = dy / distance_to_next

                # Move the remaining distance in the direction of the next waypoint (in pixels)
                self.x += dir_x * remaining_move_dist
                self.y += dir_y * remaining_move_dist
                remaining_move_dist = 0

    def has_reached_base(self) -> bool:
        return self._reached_base


class SimTower(SimEntity):
    """Simulation tower

    Towers can target and shoot at enemy units

    Attributes:
        tower_type: Type
        level: Tower level
        damage: Dps (integer)
        range_px: Attack range in pixels (float)
        cooldown_ticks: Cooldown between attacks in ticks (integer)
        current_cooldown: Remaining cooldown ticks
    """

    def __init__(
        self,
        entity_id: int,
        player_id: PlayerID,
        tower_type: str,
        x: float,
        y: float,
        level: int,
    ):
        """
        Args:
            entity_id: Unique id
            player_id: Owner player
            tower_type: Tower type identifier
            x: coordinate in pixels
            y: coordinate in pixels
            level: Tower level
        """
        super().__init__(entity_id, player_id, x, y)

        # Get tower stats
        if tower_type not in TOWER_STATS:
            raise ValueError(f"Unknown tower type: {tower_type}")
        stats = TOWER_STATS[tower_type]

        self.tower_type = tower_type
        self.level = level
        self.damage = stats["damage"]
        self.range_px = stats["range_px"]
        self.cooldown_ticks = stats["cooldown_ticks"]
        self.current_cooldown = 0

    def update(self, enemy_units: list[SimUnit], game_state: "GameState") -> None:
        """Update tower (cooldown and shooting)

        Args:
            enemy_units: List of enemy units to potentially target
        """
        if not self.is_active:
            return

        # Update cooldown (in ticks)
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

        # Try to shoot if cooldown is ready
        if self.current_cooldown == 0:
            target = self._find_target(enemy_units)

            if target is not None:
                self._shoot(target, game_state)
                self.current_cooldown = self.cooldown_ticks

    def _find_target(self, enemy_units: list[SimUnit]) -> SimUnit | None:
        """Closest enemy unit in range, or None"""
        closest_unit = None
        closest_distance = float("inf")

        for unit in enemy_units:
            if not unit.is_active:
                continue

            # Only target enemy units
            if unit.player_id == self.player_id:
                continue

            distance = self.distance_to(unit.x, unit.y)
            if distance <= self.range_px and distance < closest_distance:
                closest_distance = distance
                closest_unit = unit

        return closest_unit

    def _shoot(self, target: SimUnit, game_state: "GameState") -> None:
        """Shoot at target unit"""
        target.take_damage(self.damage, self.player_id, game_state)


class GameState:
    """Deterministic single-round simulation state"""

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
        """Advance simulation by one tick"""

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
                    self.lives_lost_player_B += 1
                else:
                    self.lives_lost_player_A += 1

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
        """Check if simulation is complete using timed end condition

        Rules:
        - Must run for at least 5 seconds (min_duration_ticks)
        - After the last unit is inactive and no units pending, wait 3 seconds
        """
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
