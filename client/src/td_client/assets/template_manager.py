from typing import Dict, List, Optional, Tuple

import pygame

from .asset_loader import AssetLoader
from ..config import GameSettings
from td_shared.game import PlayerID


class TemplateManager:
    """Manages creation and access to render templates and shared assets."""

    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        self._unit_templates: Dict[Tuple[str, PlayerID], dict[str, List[pygame.Surface]]] = {}
        self._tower_templates: Dict[str, pygame.Surface] = {}

    def preload_templates(self) -> None:
        """Preload static templates that are not player dependent."""
        self._load_tower_templates()

    def _load_tower_templates(self) -> None:
        """Load real tower images instead of drawing rectangles."""
        # Load the blue tower image
        # Using scale_factor=0.5 because the original assets are quite large
        img = self.asset_loader.load_image(
            self.asset_loader.paths.tower_blue,
            scale_factor=0.5,
        )
        self._tower_templates["standard"] = img

    def get_tower_template(self, tower_type: str) -> Optional[pygame.Surface]:
        return self._tower_templates.get(tower_type)

    def get_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> dict[str, List[pygame.Surface]]:
        """Get (and cache) animation frames for a unit type."""
        cache_key = (unit_type, player_id)

        if cache_key not in self._unit_templates:
            self._unit_templates[cache_key] = self._create_unit_template(
                unit_type, player_id
            )

        return self._unit_templates[cache_key]

    def _create_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> dict[str, List[pygame.Surface]]:
        """Create and load animation frames for a unit type."""

        frame_count = 6

        # Tiny Swords sprite sheet mapping (based on the asset layout):
        # Row 0 = Idle
        # Row 1 = Run
        # Row 2 = Attack Side 1 (Right)
        # Row 4 = Attack Down 1
        # Row 6 = Attack Up 1

        if player_id == "A":
            path = self.asset_loader.paths.warrior_blue
        else:
            path = self.asset_loader.paths.warrior_red

        # Create fallback animation (used if loading fails)
        fallback = pygame.Surface((40, 40))
        fallback.fill((255, 0, 0))
        animations = {
            "idle": [fallback],
            "run": [fallback],
            "atk_side": [fallback],
            "atk_down": [fallback],
            "atk_up": [fallback],
        }

        # If the asset path does not exist, return fallback animations
        if not path.exists():
            return animations

        try:
            # Load all required animation rows from the sprite sheet
            animations["idle"] = self.asset_loader.load_grid_row(
                path, row_index=0, frame_count=frame_count, scale_factor=0.5
            )
            animations["run"] = self.asset_loader.load_grid_row(
                path, row_index=1, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_side"] = self.asset_loader.load_grid_row(
                path, row_index=2, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_down"] = self.asset_loader.load_grid_row(
                path, row_index=4, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_up"] = self.asset_loader.load_grid_row(
                path, row_index=6, frame_count=frame_count, scale_factor=0.5
            )
            return animations

        except Exception as e:
            print(f"Error loading unit assets from {path}: {e}")
            return animations

    def get_water_tile(self, tile_size: int) -> pygame.Surface:
        water_image = self.asset_loader.load_image(self.asset_loader.paths.water)
        original_width, original_height = water_image.get_size()

        if original_width != tile_size or original_height != tile_size:
            water_image = pygame.transform.scale(
                water_image, (tile_size, tile_size)
            )

        return water_image

    def get_foam_frames(self, frame_count: int) -> List[pygame.Surface]:
        return self.asset_loader.load_spritesheet(
            self.asset_loader.paths.foam,
            frame_count=frame_count,
            direction="horizontal",
        )

    def get_path_tile_image(self) -> pygame.Surface:
        surface = pygame.Surface((64, 64), pygame.SRCALPHA)
        surface.fill((180, 140, 100, 255))

        pygame.draw.rect(
            surface, (140, 110, 80, 255), surface.get_rect(), 4
        )
        return surface

    def get_castle_images(
        self, settings: GameSettings
    ) -> Tuple[pygame.Surface, pygame.Surface]:
        castle_blue_image = self.asset_loader.load_image(
            self.asset_loader.paths.castle_blue,
            scale_factor=settings.default_sprite_scale,
        )

        castle_red_image = self.asset_loader.load_image(
            self.asset_loader.paths.castle_red,
            scale_factor=settings.default_sprite_scale,
        )
        return castle_blue_image, castle_red_image
    
    def get_effect_template(self, effect_name: str) -> list[pygame.Surface]:
        """Loads frames for one-shot effects."""
        
        frames = []
        
        if effect_name == "spawn_dust":
            # Dust_02.png has 10 columns
            try:
                frames = self.asset_loader.load_grid_row(
                    self.asset_loader.paths.spawn_dust, 
                    row_index=0, 
                    frame_count=10, 
                    scale_factor=1.0 # Adjust scale if dust is too big/small
                )
            except Exception:
                print("Failed to load Spawn Dust")

        elif effect_name == "explosion":
            # Explosions.png has 9 columns
            try:
                frames = self.asset_loader.load_grid_row(
                    self.asset_loader.paths.explosion, 
                    row_index=0, 
                    frame_count=9, 
                    scale_factor=1.0
                )
            except Exception:
                print("Failed to load Explosion")
                
        # Fallback if loading failed
        if not frames:
            s = pygame.Surface((20, 20))
            s.fill((255, 255, 0)) # Yellow square fallback
            frames = [s]
            
        return frames
