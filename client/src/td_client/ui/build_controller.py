from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared.game import TILE_SIZE_PX, TOWER_STATS, UNIT_STATS

from td_client.events import (
    BuildTowerResponseEvent,
    EventBus,
    GoldChangedEvent,
    HoverTileChangedEvent,
    RequestBuildTowerEvent,
    RequestSendUnitsEvent,
    RouteHoverChangedEvent,
    SendUnitsResponseEvent,
    ToggleBuildModeEvent,
)

if TYPE_CHECKING:
    from ..simulation.game_simulation import GameSimulation

logger = logging.getLogger(__name__)


class BuildController:
    """Handles build mode interactions.

    This controller ONLY publishes events to the EventBus.
    It does NOT:
    - Access NetworkClient directly (NetworkHandler does that)
    - Manipulate game state without publishing corresponding events

    The flow is:
    1. User clicks -> BuildController publishes RequestBuildTowerEvent
    2. NetworkHandler receives event, calls NetworkClient
    3. NetworkHandler publishes BuildTowerResponseEvent
    4. BuildController handles response (rollback if failed)
    """

    def __init__(self, game: GameSimulation):
        self.game = game
        self.event_bus: EventBus | None = game.event_bus
        self._subscriptions: list = []

        # Subscribe to server response events
        if self.event_bus:
            self._subscriptions.append(
                self.event_bus.subscribe(
                    BuildTowerResponseEvent, self._on_build_tower_response
                )
            )
            self._subscriptions.append(
                self.event_bus.subscribe(
                    SendUnitsResponseEvent, self._on_send_units_response
                )
            )

    def cleanup(self) -> None:
        """Unsubscribe from all events."""
        for unsub in self._subscriptions:
            unsub()
        self._subscriptions.clear()

    def _get_my_map_and_grid(self, game=None):
        target = game or self.game
        return target.terrain_map, target.get_player_grid(target.player_id)

    def handle_mouse_motion(self, event, game) -> None:
        """Handle mouse motion - updates hover tile and route hover via events."""
        mx, my = event.pos
        my_map, my_grid = self._get_my_map_and_grid(game)

        # Check for route button hover
        old_hovered_route = game.ui_state.hovered_route
        new_hovered_route = None
        buttons = game.ui_state.barracks_buttons
        for idx, rect in enumerate(buttons, start=1):
            if rect.collidepoint(mx, my):
                new_hovered_route = idx
                break

        # Update route hover state and publish event if changed
        if old_hovered_route != new_hovered_route:
            game.ui_state.hovered_route = new_hovered_route
            if self.event_bus:
                self.event_bus.publish(RouteHoverChangedEvent(route=new_hovered_route))

        # Check for tile hover (for build mode)
        old_hover = game.ui_state.hover_tile
        new_hover = None

        # Track tower button hover for better visual feedback
        game.ui_state.tower_button_hovered = (
            game.ui_state.tower_button.collidepoint(mx, my)
            if game.ui_state.tower_button
            else False
        )

        if my_map.rect.collidepoint(mx, my):
            local_x = mx - my_map.rect.x
            local_y = my - my_map.rect.y
            row, col = my_grid.pixel_to_grid_coords(local_x, local_y)
            if my_grid.is_buildable(row, col):
                new_hover = (row, col)

        # Update state and publish event if changed
        if old_hover != new_hover:
            game.ui_state.hover_tile = new_hover
            if self.event_bus:
                self.event_bus.publish(HoverTileChangedEvent(tile=new_hover))

    def handle_mouse_click(self, event, game) -> None:
        """Handle mouse click - publishes appropriate events."""
        mx, my = event.pos

        # Priority 1: Send units buttons (unverändert)
        for idx, rect in enumerate(game.ui_state.barracks_buttons, start=1):
            if rect.collidepoint(mx, my):
                import time

                game.ui_state.last_clicked_route = idx
                game.ui_state.click_time = time.time()
                self._request_send_units(game, idx)
                return

        # Priority 2: Unit Selection Buttons (unverändert)
        for rect, u_type in game.ui_state.unit_selection_buttons:
            if rect.collidepoint(mx, my):
                game.ui_state.selected_unit_type = u_type
                return

        # Priority 3: Building Selection Buttons
        # NEU: Aktiviert jetzt sofort den Baumodus
        for rect, b_type in game.ui_state.building_selection_buttons:
            if rect.collidepoint(mx, my):
                game.ui_state.selected_building_type = b_type
                game.ui_state.tower_build_mode = True  # Sofort aktivieren
                logger.info(f"Building selected: {b_type}, Build Mode ON")
                return

        # Priority 4: Tower placement (Wenn Modus an ist)
        if game.ui_state.tower_build_mode:
            self._request_build_tower(game, mx, my)

    def _toggle_build_mode(self, game) -> None:
        """Toggle build mode and publish event."""
        new_mode = not game.ui_state.tower_build_mode
        game.ui_state.tower_build_mode = new_mode

        if not new_mode:
            game.ui_state.hover_tile = None

        logger.info("Tower build mode: %s", "ON" if new_mode else "OFF")

        if self.event_bus:
            self.event_bus.publish(ToggleBuildModeEvent(enabled=new_mode))

    def _request_send_units(self, game, route: int) -> None:
        """Request to send units - publishes event, does NOT call network directly."""
        unit_type_to_send = game.ui_state.selected_unit_type

        try:
            unit_cost = int(UNIT_STATS[unit_type_to_send]["cost"])
        except (KeyError, ValueError):
            logger.error(f"Could not find cost for unit type: {unit_type_to_send}")
            return

        # Check if player has enough gold locally
        if game.player_state.my_gold < unit_cost:
            logger.warning(
                f"Not enough gold to send unit. Have {game.player_state.my_gold}, need {unit_cost}."
            )
            return

        # Optimistic gold deduction
        game.player_state.my_gold -= unit_cost

        # Trigger green flash on gold display
        game.ui_state.gold_flash_timer = 0.5
        game.ui_state.gold_flash_color = (255, 100, 100)  # Red flash for spend
        game.ui_state.gold_display_scale = 1.2  # Pulse effect

        logger.info(
            f"Barracks button clicked: route {route}. Optimistically deducted {unit_cost} gold."
        )

        # Publish gold changed event
        if self.event_bus:
            self.event_bus.publish(
                GoldChangedEvent(
                    player_id=game.player_id,
                    new_gold=game.player_state.my_gold,
                    delta=-unit_cost,
                )
            )

        # Publish request event - NetworkHandler will handle the network call
        if self.event_bus:
            # Track locally for UI preview
            game.ui_state.route_unit_previews.setdefault(route, []).append(
                unit_type_to_send
            )
            self.event_bus.publish(
                RequestSendUnitsEvent(
                    player_id=game.player_id,
                    unit_type=unit_type_to_send,
                    route=route,
                    spawn_tick=0,
                )
            )
        else:
            logger.error("No event bus available - cannot send units request")

    def _request_build_tower(self, game, mx: int, my: int) -> None:
        """Request to build tower - publishes event, does NOT call network directly."""
        # Can only build during preparation phase
        if not game.phase_state.in_preparation:
            logger.warning("Cannot build during combat phase")
            return

        my_map, my_grid = self._get_my_map_and_grid(game)
        if not my_map.rect.collidepoint(mx, my):
            return

        local_x = mx - my_map.rect.x
        local_y = my - my_map.rect.y
        row, col = my_grid.pixel_to_grid_coords(local_x, local_y)

        # Get the selected building type
        building_type = game.ui_state.selected_building_type
        tower_stats = TOWER_STATS.get(building_type)
        if not tower_stats:
            logger.warning("Unknown building type: %s", building_type)
            return
        tower_cost = int(tower_stats["cost"])

        # Validation: Check all build conditions
        validation_checks = [
            (
                "tile_buildable",
                my_grid.is_buildable(row, col),
                f"Cannot build tower at ({row},{col}) - tile not buildable",
            ),
            (
                "enough_gold",
                game.player_state.my_gold >= tower_cost,
                f"Not enough gold to build tower. Have {game.player_state.my_gold}, need {tower_cost}.",
            ),
        ]

        # check if all validations pass
        if not all(check[1] for check in validation_checks):
            # Find first failed check and log warning
            failed_check = next(
                (check for check in validation_checks if not check[1]), None
            )
            if failed_check:
                logger.warning(failed_check[2])
            return

        # Capture state before build attempt for rollback
        was_empty = True  # We already validated it's buildable
        sprite_existed = (game.player_id, row, col) in game.ui_state.local_towers
        if building_type == "gold_mine":
            sprite_existed = (
                game.player_id,
                row,
                col,
            ) in game.ui_state.local_gold_mines

        # Optimistic updates
        old_gold = game.player_state.my_gold
        game.player_state.my_gold -= tower_cost

        # Precondition: Must have enough gold
        assert (
            old_gold >= tower_cost
        ), f"Must have enough gold: have {old_gold}, need {tower_cost}"

        # Postcondition: Gold should be deducted
        assert (
            game.player_state.my_gold == old_gold - tower_cost
        ), f"Gold not correctly deducted: expected {old_gold - tower_cost}, got {game.player_state.my_gold}"

        # Trigger green flash on gold display
        game.ui_state.gold_flash_timer = 0.5
        game.ui_state.gold_flash_color = (255, 100, 100)  # Red flash for spend
        game.ui_state.gold_display_scale = 1.2  # Pulse effect

        my_grid.place_tower(row, col)
        sprite_created = self.spawn_tower(game.player_id, row, col, building_type)

        # Postcondition: If sprite was created, it should exist in appropriate dict
        key = (game.player_id, row, col)
        if sprite_created:
            if building_type == "gold_mine":
                assert (
                    key in game.ui_state.local_gold_mines
                ), f"Gold mine should exist in local_gold_mines after creation at ({row}, {col})"
            else:
                assert (
                    key in game.ui_state.local_towers
                ), f"Tower should exist in local_towers after creation at ({row}, {col})"

        logger.info(
            "Placing %s at (%d,%d), sending request... (sprite existed: %s, created: %s)",
            building_type,
            row,
            col,
            sprite_existed,
            sprite_created,
        )

        # Publish gold changed event
        if self.event_bus:
            self.event_bus.publish(
                GoldChangedEvent(
                    player_id=game.player_id,
                    new_gold=game.player_state.my_gold,
                    delta=-tower_cost,
                )
            )

        # Publish request event - NetworkHandler will handle the network call
        if self.event_bus:
            self.event_bus.publish(
                RequestBuildTowerEvent(
                    player_id=game.player_id,
                    tower_type=building_type,
                    tile_row=row,
                    tile_col=col,
                    was_empty=was_empty,
                    sprite_existed=sprite_existed,
                )
            )
        else:
            logger.error("No event bus available - cannot send build tower request")

        # Check if shift is held - if so, stay in build mode
        mods = pygame.key.get_mods()
        shift_held = bool(mods & pygame.KMOD_SHIFT)
        
        if not shift_held:
            # Exit build mode only if shift is not held
            game.ui_state.tower_build_mode = False
            game.ui_state.hover_tile = None

            if self.event_bus:
                self.event_bus.publish(ToggleBuildModeEvent(enabled=False))

    def _on_build_tower_response(self, event: BuildTowerResponseEvent) -> None:
        """Handle build tower response - rollback if failed."""
        # Preconditions
        assert event is not None, "event must not be None"
        assert event.tile_row >= 0, f"tile_row must be >= 0, not {event.tile_row}"
        assert event.tile_col >= 0, f"tile_col must be >= 0, not {event.tile_col}"
        assert (
            event.tower_type in TOWER_STATS
        ), f"tower_type must exist in TOWER_STATS, not '{event.tower_type}'"

        if event.success:
            logger.info(
                "BuildTower succeeded at (%d,%d)", event.tile_row, event.tile_col
            )
            # Postcondition: If we optimistically created a sprite, it should still exist
            if not event.sprite_existed:
                key = (self.game.player_id, event.tile_row, event.tile_col)
                if event.tower_type == "gold_mine":
                    assert (
                        key in self.game.ui_state.local_gold_mines
                    ), f"Gold mine should exist at ({event.tile_row}, {event.tile_col}) after success"
                else:
                    assert (
                        key in self.game.ui_state.local_towers
                    ), f"Tower should exist at ({event.tile_row}, {event.tile_col}) after success"
            return

        logger.warning(
            "BuildTower rejected at (%d,%d), rolling back",
            event.tile_row,
            event.tile_col,
        )

        # Rollback gold based on the tower type that was attempted
        tower_stats = TOWER_STATS.get(event.tower_type, TOWER_STATS["standard"])
        tower_cost = int(tower_stats["cost"])
        old_gold = self.game.player_state.my_gold
        self.game.player_state.my_gold += tower_cost

        # Postcondition: Gold should be refunded
        assert (
            self.game.player_state.my_gold == old_gold + tower_cost
        ), f"Gold not correctly refunded: expected {old_gold + tower_cost}, got {self.game.player_state.my_gold}"

        # Trigger green flash on gold display (refund)
        self.game.ui_state.gold_flash_timer = 0.5
        self.game.ui_state.gold_flash_color = (100, 255, 100)  # Green flash for gain
        self.game.ui_state.gold_display_scale = 1.2  # Pulse effect

        if self.event_bus:
            self.event_bus.publish(
                GoldChangedEvent(
                    player_id=self.game.player_id,
                    new_gold=self.game.player_state.my_gold,
                    delta=tower_cost,
                )
            )

        # Rollback sprite
        key = (self.game.player_id, event.tile_row, event.tile_col)
        sprite_exists_now = False
        if event.tower_type == "gold_mine":
            sprite_exists_now = key in self.game.ui_state.local_gold_mines
        else:
            sprite_exists_now = key in self.game.ui_state.local_towers

        # Always remove sprite if it exists (optimistic creation should be rolled back)
        if sprite_exists_now:
            self.remove_tower(
                self.game.player_id, event.tile_row, event.tile_col, event.tower_type
            )
            logger.info(
                "Rolled back %s at (%d,%d) - removed sprite",
                event.tower_type,
                event.tile_row,
                event.tile_col,
            )
            # Postcondition: Sprite should be removed
            if event.tower_type == "gold_mine":
                assert (
                    key not in self.game.ui_state.local_gold_mines
                ), f"Gold mine should be removed from local_gold_mines at ({event.tile_row}, {event.tile_col})"
            else:
                assert (
                    key not in self.game.ui_state.local_towers
                ), f"Tower should be removed from local_towers at ({event.tile_row}, {event.tile_col})"

        # Rollback grid if it was empty
        if event.was_empty:
            my_grid = self.game.get_player_grid(self.game.player_id)
            my_grid.clear_tower(event.tile_row, event.tile_col)
            logger.info(
                "Rolled back tower at (%d,%d) - cleared grid",
                event.tile_row,
                event.tile_col,
            )

    def _on_send_units_response(self, event: SendUnitsResponseEvent) -> None:
        """Handle send units response - sync gold with server."""
        if event.success and event.total_gold is not None:
            logger.info("SendUnits acknowledged, syncing gold to %d", event.total_gold)
            old_gold = self.game.player_state.my_gold
            self.game.player_state.my_gold = event.total_gold

            if self.event_bus:
                self.event_bus.publish(
                    GoldChangedEvent(
                        player_id=self.game.player_id,
                        new_gold=event.total_gold,
                        delta=event.total_gold - old_gold,
                    )
                )
        elif not event.success and event.total_gold is not None:
            # Server rejected - sync to server's gold value
            logger.warning("SendUnits rejected, syncing gold to %d", event.total_gold)
            old_gold = self.game.player_state.my_gold
            self.game.player_state.my_gold = event.total_gold
            # Roll back last preview for the route if we added one
            if event.route is not None:
                previews = self.game.ui_state.route_unit_previews.get(event.route)
                if previews:
                    previews.pop()

            if self.event_bus:
                self.event_bus.publish(
                    GoldChangedEvent(
                        player_id=self.game.player_id,
                        new_gold=event.total_gold,
                        delta=event.total_gold - old_gold,
                    )
                )

    def spawn_tower(self, player_id: str, row: int, col: int, tower_type: str) -> bool:
        """Spawn a tower sprite. Returns True if new sprite was created."""
        key = (player_id, row, col)

        # Check if sprite already exists in appropriate dict
        if tower_type == "gold_mine":
            if key in self.game.ui_state.local_gold_mines:
                return False
        else:
            if key in self.game.ui_state.local_towers:
                return False

        tmap = self.game.terrain_map
        tower_info = TOWER_STATS.get(tower_type)
        range_px = float(tower_info["range_px"]) if tower_info else 120.0

        x = tmap.rect.x + col * TILE_SIZE_PX + TILE_SIZE_PX / 2.0
        y = tmap.rect.y + row * TILE_SIZE_PX + TILE_SIZE_PX

        tm = self.game.render_manager.template_manager
        sprite = None

        if tower_type == "standard":
            from ..sprites.buildings import MannedTowerSprite

            image = tm.get_tower_template(tower_type, player_id)
            if image is None:
                return False

            archer_anims = tm.get_unit_template("archer", player_id)

            sprite = MannedTowerSprite(
                x=x,
                y=y,
                image=image,
                archer_anims=archer_anims,
                player_id=player_id,
                range_px=range_px,
            )

            self.game.render_manager.animation_manager.register(sprite)
            self.game.render_manager.buildings.add(sprite)
            self.game.ui_state.local_towers[key] = sprite

        elif tower_type == "wood_tower":
            from ..sprites.buildings import AnimatedTowerSprite

            tower_frames = tm.get_wood_tower_frames(player_id)
            if not tower_frames:
                return False

            archer_anims = tm.get_unit_template("archer", player_id)

            sprite = AnimatedTowerSprite(
                x=x,
                y=y,
                tower_frames=tower_frames,
                archer_anims=archer_anims,
                player_id=player_id,
                range_px=range_px,
                archer_offset_y=-30,  # Slightly different offset for wood tower
            )

            self.game.render_manager.animation_manager.register(sprite)
            self.game.render_manager.buildings.add(sprite)
            self.game.ui_state.local_towers[key] = sprite

        elif tower_type == "gold_mine":
            from ..sprites.buildings import GoldMineSprite

            gold_mine_images = tm.get_gold_mine_images()
            if not gold_mine_images:
                return False

            sprite = GoldMineSprite(
                x=x,
                y=y,
                active_image=gold_mine_images["active"],
                inactive_image=gold_mine_images["inactive"],
            )

            # Set mine inactive if currently in combat phase
            if self.game.phase_state.in_combat:
                sprite.set_active(False)

            self.game.render_manager.buildings.add(sprite)
            self.game.ui_state.local_gold_mines[key] = sprite
        else:
            # Fallback for other towers (static)
            from ..sprites.buildings import BuildingSprite

            image = tm.get_tower_template(tower_type, player_id)
            if image is None:
                return False
            sprite = BuildingSprite(x=x, y=y, image=image, range_px=range_px)
            self.game.render_manager.buildings.add(sprite)
            self.game.ui_state.local_towers[key] = sprite

        return True

    def remove_tower(
        self, player_id: str, row: int, col: int, tower_type: str = "standard"
    ) -> None:
        """Remove a tower sprite."""
        key = (player_id, row, col)

        if tower_type == "gold_mine":
            sprite = self.game.ui_state.local_gold_mines.pop(key, None)
        else:
            sprite = self.game.ui_state.local_towers.pop(key, None)

        if sprite:
            # If it was animated, we must unregister it
            if hasattr(sprite, "update_animation"):
                self.game.render_manager.animation_manager.unregister(sprite)

            sprite.kill()
