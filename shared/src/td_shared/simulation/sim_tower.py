"""Simulation tower implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..game.game_balance import TOWER_STATS
from ..game.protocol import PlayerID
from .sim_entity import SimEntity

if TYPE_CHECKING:
    from .game_state import GameState
    from .sim_unit import SimUnit


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
