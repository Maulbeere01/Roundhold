"""Simulation entity implementations (units and towers)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ..game.game_balance import (
    GAME_PATHS,
    TILE_SIZE_PX,
    TOWER_STATS,
    UNIT_STATS,
    tile_to_pixel,
)
from ..game.protocol import PlayerID
from .base import SimEntity

if TYPE_CHECKING:
    from .game_state import GameState


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
        # Preconditions
        assert entity_id >= 0, f"entity_id must be >= 0, not {entity_id}"
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert route >= 1, f"route must be >= 1, not {route}"
        assert sim_dt > 0, f"sim_dt must be > 0, not {sim_dt}"

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

        # Store initial spawn offset for easing into path
        self.spawn_offset_x = 0.0
        self.spawn_offset_y = 0.0
        self.ease_progress = 1.0  # 0-1, where 1 = fully on path

        self.unit_type = unit_type
        self.route = route
        self.max_health = stats["health"]
        self.health = self.max_health
        self.speed = stats["speed"]
        self.base_damage = stats.get("base_damage", 1)
        self.path = path_pixels
        self.current_path_index = 0
        self.sim_dt = sim_dt
        self._reached_base = False

        # Postconditions
        assert len(self.path) > 0, "Path must not be empty"
        assert (
            self.health == self.max_health
        ), "health must equal max_health after initialization"

    def take_damage(
        self, damage: int, attacker_player_id: PlayerID, game_state: GameState
    ) -> None:
        """Apply damage and record kill attribution on death."""
        # Preconditions
        assert damage >= 0, f"damage must be >= 0, not {damage}"
        assert attacker_player_id in (
            "A",
            "B",
        ), f"attacker_player_id must be 'A' or 'B', not '{attacker_player_id}'"
        assert (
            self.health > 0
        ), f"Unit must be alive to take damage, health: {self.health}"

        old_health = self.health
        was_alive = self.health > 0
        old_kills_A = game_state.kills_by_player_A
        old_kills_B = game_state.kills_by_player_B

        self.health -= damage

        if self.health <= 0:
            self.health = 0
            self.is_active = False
            # count kills for gold distribution
            if attacker_player_id == "A":
                game_state.kills_by_player_A += 1
            else:
                game_state.kills_by_player_B += 1

        # Postconditions
        assert self.health == max(
            0, old_health - damage
        ), "health not correctly reduced"
        if was_alive and self.health <= 0:
            assert not self.is_active, "Unit must be inactive when health <= 0"
            if attacker_player_id == "A":
                assert (
                    game_state.kills_by_player_A == old_kills_A + 1
                ), "Kills not correctly incremented for player A"
            else:
                assert (
                    game_state.kills_by_player_B == old_kills_B + 1
                ), "Kills not correctly incremented for player B"

    def update(self) -> None:
        """Update unit position (deterministic movement along path)."""
        # Preconditions
        assert self.current_path_index < len(
            self.path
        ), f"current_path_index must be < path length, not {self.current_path_index}"

        if not self.is_active:
            return

        # Handle easing from spawn offset into path
        if self.ease_progress < 1.0:
            ease_speed = 3.0  # How fast to ease (units per second)
            self.ease_progress = min(1.0, self.ease_progress + ease_speed * self.sim_dt)
            # Lerp from offset position to path start
            path_start = self.path[0]
            offset_x = path_start[0] + self.spawn_offset_x
            offset_y = path_start[1] + self.spawn_offset_y
            self.x = offset_x + (path_start[0] - offset_x) * self.ease_progress
            self.y = offset_y + (path_start[1] - offset_y) * self.ease_progress
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
                assert (
                    distance_to_next > 0
                ), "distance_to_next must be > 0 for direction calculation"
                dir_x = dx / distance_to_next
                dir_y = dy / distance_to_next

                # Move the remaining distance in the direction of the next waypoint (in pixels)
                self.x += dir_x * remaining_move_dist
                self.y += dir_y * remaining_move_dist
                remaining_move_dist = 0

        # Postcondition
        assert self.current_path_index < len(
            self.path
        ), "current_path_index must be < path length after update"

    def has_reached_base(self) -> bool:
        return self._reached_base


class SimTower(SimEntity):
    """Simulation tower."""

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
        # Preconditions
        assert entity_id >= 0, f"entity_id must be >= 0, not {entity_id}"
        assert player_id in (
            "A",
            "B",
        ), f"player_id must be 'A' or 'B', not '{player_id}'"
        assert level >= 1, f"level must be >= 1, not {level}"

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
        self.last_shot_target: tuple[float, float] | None = None
        self.shoot_anim_timer = 0

    def update(self, enemy_units: list[SimUnit], game_state: GameState) -> None:
        """Update tower (cooldown and shooting)."""
        if not self.is_active:
            return

        # Decrement visual timer
        if self.shoot_anim_timer > 0:
            self.shoot_anim_timer -= 1
        else:
            self.last_shot_target = None

        # Update cooldown (in ticks)
        if self.current_cooldown > 0:
            self.current_cooldown -= 1

        # Try to shoot if cooldown is ready
        if self.current_cooldown == 0:
            target = self._find_target(enemy_units)

            if target is not None:
                assert target.player_id != self.player_id, "Target must be enemy unit"
                self._shoot(target, game_state)
                self.current_cooldown = self.cooldown_ticks

                self.last_shot_target = (target.x, target.y)
                # Keep the aiming/attack animation alive for the whole cooldown to avoid choppy resets
                self.shoot_anim_timer = max(8, self.cooldown_ticks)

    def _find_target(self, enemy_units: list[SimUnit]) -> SimUnit | None:
        """Closest enemy unit in range, or None."""
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

    def _shoot(self, target: SimUnit, game_state: GameState) -> None:
        """Shoot at target unit."""
        # Preconditions
        assert target.player_id != self.player_id, "target must be enemy unit"
        assert self.damage >= 0, f"damage must be >= 0, not {self.damage}"

        old_target_health = target.health

        # Track projectile for visual rendering
        if not hasattr(game_state, "pending_projectiles"):
            game_state.pending_projectiles = []
        game_state.pending_projectiles.append(
            {
                "from_x": self.x,
                "from_y": self.y,
                "to_x": target.x,
                "to_y": target.y,
                "damage": self.damage,
            }
        )

        target.take_damage(self.damage, self.player_id, game_state)

        # Postcondition
        assert (
            target.health <= old_target_health
        ), "Target health must not increase after taking damage"
