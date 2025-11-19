from __future__ import annotations

import logging

from td_shared.game import TILE_SIZE_PX, TOWER_STATS, UNIT_STATS

logger = logging.getLogger(__name__)


class BuildController:
    """Handles build mode interactions"""

    def __init__(self, game):
        self.game = game
        self.network_client = game.network_client

    def _get_my_map_and_grid(self, game=None):
        target = game or self.game
        return target.map_state.terrain_map, target.get_player_grid(target.player_id)

    def handle_mouse_motion(self, event, game) -> None:
        mx, my = event.pos
        my_map, my_grid = self._get_my_map_and_grid(game)
        if my_map.rect.collidepoint(mx, my):
            local_x = mx - my_map.rect.x
            local_y = my - my_map.rect.y
            row, col = my_grid.pixel_to_grid_coords(local_x, local_y)
            if my_grid.is_buildable(row, col):
                game.ui_state.hover_tile = (row, col)
            else:
                game.ui_state.hover_tile = None
        else:
            game.ui_state.hover_tile = None

    def handle_mouse_click(self, event, game) -> None:
        mx, my = event.pos
        # Ranked by priority
        # Tower button (toggle build mode)
        if game.ui_state.tower_button.collidepoint(mx, my):
            game.ui_state.tower_build_mode = not game.ui_state.tower_build_mode
            if not game.ui_state.tower_build_mode:
                game.ui_state.hover_tile = None
            logger.info(
                "Tower build mode: %s",
                "ON" if game.ui_state.tower_build_mode else "OFF",
            )
            return

        # Send units buttons
        for idx, rect in enumerate(game.ui_state.barracks_buttons, start=1):
            if rect.collidepoint(mx, my):
                #    Get the cost of the unit. Currently hardcoded as 'standard'.
                #    If there are different units, this should be dynamic.
                unit_type_to_send = "standard"
                try:
                    unit_cost = int(UNIT_STATS[unit_type_to_send]["cost"])
                except (KeyError, ValueError):
                    logger.error(
                        f"Could not find cost for unit type: {unit_type_to_send}"
                    )
                    return  # Cancel action if unit type is unknown

                # check if player has enough gold locally
                if game.player_state.my_gold >= unit_cost:
                    # predict gold usage
                    game.player_state.my_gold -= unit_cost
                    logger.info(
                        f"Barracks button clicked: route {idx}. Optimistically deducted {unit_cost} gold."
                    )

                    # Send network request to server
                    self.network_client.send_units(
                        player_id=game.player_id,
                        units=[
                            {
                                "unit_type": unit_type_to_send,
                                "route": idx,
                                "spawn_tick": 0,
                            }
                        ],
                        on_done=game._on_send_units_response,
                    )
                    logger.debug(f"SendUnits dispatched for route {idx}")

                else:
                    logger.warning(
                        f"Not enough gold to send unit (local check). Have {game.player_state.my_gold}, need {unit_cost}."
                    )

                return

        # Tower placement
        if game.ui_state.tower_build_mode:
            my_map, my_grid = self._get_my_map_and_grid(game)
            if my_map.rect.collidepoint(mx, my):
                local_x = mx - my_map.rect.x
                local_y = my - my_map.rect.y
                row, col = my_grid.pixel_to_grid_coords(local_x, local_y)
                tower_cost = int(TOWER_STATS["standard"]["cost"])
                # Capture state before build attempt for rollback
                was_empty = my_grid.is_buildable(row, col)
                sprite_existed = (
                    game.player_id,
                    row,
                    col,
                ) in game.ui_state.local_towers
                # always try to build, server will validate
                game.player_state.my_gold -= tower_cost
                my_grid.place_tower(row, col)
                sprite_created = self.spawn_tower(game.player_id, row, col, "standard")
                logger.info(
                    "Placing tower at (%d,%d), sending to server... (sprite existed: %s, created: %s)",
                    row,
                    col,
                    sprite_existed,
                    sprite_created,
                )
                self.network_client.build_tower(
                    player_id=game.player_id,
                    tower_type="standard",
                    tile_row=row,
                    tile_col=col,
                    on_done=lambda success,
                    r=row,
                    c=col,
                    was_e=was_empty,
                    spr_ex=sprite_existed: game._on_build_response(
                        success, row=r, col=c, was_empty=was_e, sprite_existed=spr_ex
                    ),
                )
                game.ui_state.tower_build_mode = False
                game.ui_state.hover_tile = None

    def spawn_tower(self, player_id: str, row: int, col: int, tower_type: str) -> bool:
        """Spawn a tower sprite. Returns True if a new sprite was created, False if one already existed."""
        key = (player_id, row, col)
        if key in self.game.ui_state.local_towers:
            return False  # Sprite already exists
        tmap = self.game.map_state.terrain_map
        tower_info = TOWER_STATS.get(tower_type)
        range_px = float(tower_info["range_px"]) if tower_info else 120.0
        x = tmap.rect.x + col * TILE_SIZE_PX + TILE_SIZE_PX / 2.0
        y = tmap.rect.y + row * TILE_SIZE_PX + TILE_SIZE_PX
        image = self.game.sim_state.render_manager.template_manager.get_tower_template(
            tower_type
        )
        if image is None:
            return False
        from ..sprites.buildings import BuildingSprite

        sprite = BuildingSprite(x=x, y=y, image=image, range_px=range_px)
        self.game.sim_state.render_manager.buildings.add(sprite)
        self.game.ui_state.local_towers[key] = sprite
        return True  # New sprite created

    def remove_tower(self, player_id: str, row: int, col: int) -> None:
        key = (player_id, row, col)
        sprite = self.game.ui_state.local_towers.pop(key, None)
        if sprite:
            sprite.kill()
