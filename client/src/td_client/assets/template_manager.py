import pygame
from td_shared.game import PlayerID

from ..config import GameSettings
from .asset_loader import AssetLoader


class TemplateManager:
    """Manages creation and access to render templates and shared assets"""

    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        self._unit_templates: dict[tuple[str, PlayerID], list[pygame.Surface]] = {}
        self._tower_templates: dict[str, pygame.Surface] = {}

    def preload_templates(self) -> None:
        """Preload static templates that are not player dependent"""
        self._load_tower_templates()

    def _load_tower_templates(self) -> None:
        """Load tower asset templates for dynamic sprite creation."""
        standard_tower_surface = pygame.Surface((60, 80), pygame.SRCALPHA)
        standard_tower_surface.fill((150, 100, 50, 255))
        pygame.draw.rect(standard_tower_surface, (100, 60, 30), (10, 10, 40, 60))
        self._tower_templates["standard"] = standard_tower_surface

    def get_tower_template(self, tower_type: str) -> pygame.Surface | None:
        return self._tower_templates.get(tower_type)

    def get_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> list[pygame.Surface]:
        cache_key = (unit_type, player_id)
        if cache_key not in self._unit_templates:
            self._unit_templates[cache_key] = self._create_unit_template(
                unit_type, player_id
            )
        return self._unit_templates[cache_key]

    def _create_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> list[pygame.Surface]:
        """Create a unit template for a specific player"""
        if player_id == "A":
            unit_color = (40, 220, 40, 255)
            highlight_color = (220, 255, 220)
        else:
            unit_color = (220, 220, 40, 255)
            highlight_color = (255, 255, 220)

        unit_surface = pygame.Surface((40, 60), pygame.SRCALPHA)
        unit_surface.fill(unit_color)
        pygame.draw.circle(unit_surface, highlight_color, (20, 15), 10)
        return [unit_surface]

    def get_water_tile(self, tile_size: int) -> pygame.Surface:
        water_image = self.asset_loader.load_image(self.asset_loader.paths.water)
        original_width, original_height = water_image.get_size()
        if original_width != tile_size or original_height != tile_size:
            water_image = pygame.transform.scale(water_image, (tile_size, tile_size))
        return water_image

    def get_foam_frames(self, frame_count: int) -> list[pygame.Surface]:
        return self.asset_loader.load_spritesheet(
            self.asset_loader.paths.foam,
            frame_count=frame_count,
            direction="horizontal",
        )

    def get_path_tile_image(self) -> pygame.Surface:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        surface.fill((180, 140, 100, 255))
        pygame.draw.rect(surface, (140, 110, 80, 255), surface.get_rect(), 4)
        return surface

    def get_castle_images(
        self, settings: GameSettings
    ) -> tuple[pygame.Surface, pygame.Surface]:
        castle_blue_image = self.asset_loader.load_image(
            self.asset_loader.paths.castle_blue,
            scale_factor=settings.default_sprite_scale,
        )
        castle_red_image = self.asset_loader.load_image(
            self.asset_loader.paths.castle_red,
            scale_factor=settings.default_sprite_scale,
        )
        return castle_blue_image, castle_red_image
