from __future__ import annotations

import pygame
from td_shared.game import MAP_WIDTH_TILES, TILE_SIZE_PX


class CoordinateTranslator:
    """Converts simulation coordinates into screen coordinates."""

    def __init__(self, tilemap_provider) -> None:
        self.tilemap_provider = tilemap_provider
        self.map_width_px = MAP_WIDTH_TILES * TILE_SIZE_PX

    def set_map_width(self, width_px: int) -> None:
        self.map_width_px = width_px

    def sim_to_screen(self, entity, *, is_tower: bool) -> pygame.Vector2:
        left_map, right_map = self.tilemap_provider()
        if not left_map or not right_map:
            return pygame.Vector2(entity.x, entity.y)

        # Determine which map to render on:
        # - Player A towers on left map
        # - Player B units on left map (attacking A)
        # - Player B towers on right map
        # - Player A units on right map (attacking B)
        on_left_map = (is_tower and entity.player_id == "A") or (not is_tower and entity.player_id == "B")
        
        if on_left_map:
            map_offset_x = left_map.rect.x
            map_offset_y = left_map.rect.y
        else:
            map_offset_x = right_map.rect.x
            map_offset_y = right_map.rect.y
        
        # Handle coordinate transformation
        if is_tower:
            if entity.player_id == "B":
                sim_x = self.map_width_px - entity.x  
            else:
                sim_x = entity.x
        else:
            if entity.player_id == "B":
                sim_x = self.map_width_px - entity.x  
            else:
                sim_x = self.map_width_px - entity.x

        return pygame.Vector2(sim_x + map_offset_x, entity.y + map_offset_y)


