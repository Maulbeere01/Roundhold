from __future__ import annotations

import pygame


class MapLayerRenderer:
    """Handles drawing of static environment layers."""

    def __init__(self, animation_manager, template_manager) -> None:
        self.animation_manager = animation_manager
        self.template_manager = template_manager
        self.water_tile_surface: pygame.Surface | None = None
        self.road_renderer = None
        self.foam_renderer = None
        self.tile_size = 0
        self.screen_width = 0
        self.screen_height = 0

    def configure(self, tile_size: int, screen_width: int, screen_height: int) -> None:
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height

    def initialize_water(self) -> None:
        self.water_tile_surface = self.template_manager.get_water_tile(self.tile_size)

    def initialize_foam(self, foam_renderer) -> None:
        self.foam_renderer = foam_renderer
        if self.foam_renderer:
            self.animation_manager.register(self.foam_renderer)

    def set_road_renderer(self, road_renderer) -> None:
        self.road_renderer = road_renderer

    def draw_background(self, surface: pygame.Surface) -> None:
        if not self.water_tile_surface:
            return
        for y in range(0, self.screen_height, self.tile_size):
            for x in range(0, self.screen_width, self.tile_size):
                surface.blit(self.water_tile_surface, (x, y))

    def draw_foam(self, surface: pygame.Surface) -> None:
        if self.foam_renderer:
            foam_surface = self.foam_renderer.get_surface()
            surface.blit(foam_surface, (0, 0))

    def draw_paths(self, surface: pygame.Surface) -> None:
        if self.road_renderer and self.road_renderer.get_overlay():
            surface.blit(self.road_renderer.get_overlay(), (0, 0))