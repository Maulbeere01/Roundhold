from __future__ import annotations

import logging
import pygame
from ..map import TILE_SIZE
from td_shared.game import TOWER_STATS

logger = logging.getLogger(__name__)


class BuildController:
    """Handles build mode interactions"""

    def __init__(self, game):
        self.game = game
        self.network_client = game.network_client

    def _get_my_map_and_grid(self, game=None):
        target = game or self.game
        return target.get_player_map(target.player_id), target.get_player_grid(target.player_id)

    def handle_mouse_motion(self, event, game) -> None:
        mx, my = event.pos
        my_map, my_grid = self._get_my_map_and_grid(game)
        if my_map.rect.collidepoint(mx, my):
            local_x = mx - my_map.rect.x
            local_y = my - my_map.rect.y
            row, col = my_grid.pixel_to_grid_coords(local_x, local_y)
            if my_grid.is_buildable(row, col):
                game.hover_tile = (row, col)
            else:
                game.hover_tile = None
        else:
            game.hover_tile = None

    def handle_mouse_click(self, event, game) -> None:
        mx, my = event.pos
        # Ranked by priority
        # Tower button (toggle build mode)
        if game.tower_button.collidepoint(mx, my):
            game.tower_build_mode = not game.tower_build_mode
            if not game.tower_build_mode:
                game.hover_tile = None
            logger.info("Tower build mode: %s", "ON" if game.tower_build_mode else "OFF")
            return

        # Send units buttons
        for idx, rect in enumerate(game.barracks_buttons, start=1):
            if rect.collidepoint(mx, my):
                route = idx
                logger.info("Barracks button clicked: route %d", route)
                self.network_client.send_units(
                    player_id=game.player_id,
                    units=[{"unit_type": "standard", "route": route, "spawn_tick": 0}],
                    on_done=game._on_send_units_response,
                )
                logger.debug("SendUnits dispatched for route %d", route)
                return

        # Tower placement
        if game.tower_build_mode:
            my_map, my_grid = self._get_my_map_and_grid(game)
            if my_map.rect.collidepoint(mx, my):
                local_x = mx - my_map.rect.x
                local_y = my - my_map.rect.y
                row, col = my_grid.pixel_to_grid_coords(local_x, local_y)
                tower_cost = int(TOWER_STATS["standard"]["cost"])
                # always try to build, server will validate
                game.my_gold -= tower_cost
                my_grid.place_tower(row, col)
                self.spawn_tower(game.player_id, row, col, "standard")
                logger.info("Placing tower at (%d,%d), sending to server...", row, col)
                self.network_client.build_tower(
                    player_id=game.player_id,
                    tower_type="standard",
                    tile_row=row,
                    tile_col=col,
                    on_done=lambda success, r=row, c=col: game._on_build_response(success, row=r, col=c),
                )
                game.tower_build_mode = False
                game.hover_tile = None

    def spawn_tower(self, player_id: str, row: int, col: int, tower_type: str) -> None:
        key = (player_id, row, col)
        if key in self.game._local_towers:
            return
        tmap = self.game.get_player_map(player_id)
        tower_info = TOWER_STATS.get(tower_type)
        range_px = float(tower_info["range_px"]) if tower_info else 120.0
        x = tmap.rect.x + col * TILE_SIZE + TILE_SIZE / 2.0
        y = tmap.rect.y + row * TILE_SIZE + TILE_SIZE
        image = self.game.template_manager.get_tower_template(tower_type)
        if image is None:
            return
        from ..sprites.buildings import BuildingSprite
        sprite = BuildingSprite(x=x, y=y, image=image, range_px=range_px)
        self.game.render_manager.buildings.add(sprite)
        self.game._local_towers[key] = sprite

    def remove_tower(self, player_id: str, row: int, col: int) -> None:
        key = (player_id, row, col)
        sprite = self.game._local_towers.pop(key, None)
        if sprite:
            sprite.kill()


