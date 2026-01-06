import pygame
from td_shared.game import PlayerID

from ..config import GameSettings
from .asset_loader import AssetLoader


class TemplateManager:
    """Manages creation and access to render templates and shared assets."""

    def __init__(self, asset_loader: AssetLoader):
        self.asset_loader = asset_loader
        self._unit_templates: dict[
            tuple[str, PlayerID], dict[str, list[pygame.Surface]]
        ] = {}
        self._tower_templates: dict[str, pygame.Surface] = {}

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

    def get_tower_template(self, tower_type: str) -> pygame.Surface | None:
        return self._tower_templates.get(tower_type)

    def get_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> dict[str, list[pygame.Surface]]:
        """Get (and cache) animation frames for a unit type."""
        cache_key = (unit_type, player_id)

        if cache_key not in self._unit_templates:
            self._unit_templates[cache_key] = self._create_unit_template(
                unit_type, player_id
            )

        return self._unit_templates[cache_key]

    def _create_unit_template(
        self, unit_type: str, player_id: PlayerID
    ) -> dict[str, list[pygame.Surface]]:
        """Create and load animation frames for a unit type."""

        fallback = pygame.Surface((40, 40))
        fallback.fill((255, 0, 0))
        animations = {
            "idle": [fallback],
            "run": [fallback],
            "atk_side": [fallback],
            "atk_down": [fallback],
            "atk_up": [fallback],
        }

        path = None

        # 2. Special Logic for Archer (Load 8 frames, slice to 6)
        if unit_type == "archer":
            if player_id == "A":
                path = self.asset_loader.paths.archer_blue
            else:
                path = self.asset_loader.paths.archer_red

            if not path or not path.exists():
                return animations

            try:
                # Load 8 columns (physical layout)
                physical_cols = 8

                # Load raw rows
                idle_raw = self.asset_loader.load_grid_row(
                    path, row_index=0, frame_count=physical_cols, scale_factor=0.5
                )
                run_raw = self.asset_loader.load_grid_row(
                    path, row_index=1, frame_count=physical_cols, scale_factor=0.5
                )
                atk_up_raw = self.asset_loader.load_grid_row(
                    path, row_index=2, frame_count=physical_cols, scale_factor=0.5
                )
                atk_side_raw = self.asset_loader.load_grid_row(
                    path, row_index=4, frame_count=physical_cols, scale_factor=0.5
                )
                atk_down_raw = self.asset_loader.load_grid_row(
                    path, row_index=6, frame_count=physical_cols, scale_factor=0.5
                )

                # Slice to keep only first 6 frames (removing the empty 7th & 8th frames)
                animations["idle"] = idle_raw[:6]
                animations["run"] = run_raw[:6]
                animations["atk_up"] = atk_up_raw[:6]
                animations["atk_side"] = atk_side_raw[:6]
                animations["atk_down"] = atk_down_raw[:6]

                return animations

            except Exception as e:
                print(f"Error loading archer assets: {e}")
                return animations

        # 3. Standard Logic for other units (6 frames, no slicing needed)
        frame_count = 6

        if unit_type == "standard":  # Warrior
            if player_id == "A":
                path = self.asset_loader.paths.warrior_blue
            else:
                path = self.asset_loader.paths.warrior_red
            row_idle = 0
            row_run = 1
            row_atk_side = 2
            row_atk_down = 4
            row_atk_up = 6

        elif unit_type == "pawn":  # Pawn
            if player_id == "A":
                path = self.asset_loader.paths.pawn_blue
            else:
                path = self.asset_loader.paths.pawn_red
            row_idle = 0
            row_run = 1
            row_atk_side = 2
            row_atk_down = 2
            row_atk_up = 2

        else:
            # Fallback to warrior if type unknown
            if player_id == "A":
                path = self.asset_loader.paths.warrior_blue
            else:
                path = self.asset_loader.paths.warrior_red
            row_idle = 0
            row_run = 1
            row_atk_side = 2
            row_atk_down = 4
            row_atk_up = 6

        # Check path and load standard animations
        if not path or not path.exists():
            return animations

        try:
            animations["idle"] = self.asset_loader.load_grid_row(
                path, row_index=row_idle, frame_count=frame_count, scale_factor=0.5
            )
            animations["run"] = self.asset_loader.load_grid_row(
                path, row_index=row_run, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_side"] = self.asset_loader.load_grid_row(
                path, row_index=row_atk_side, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_down"] = self.asset_loader.load_grid_row(
                path, row_index=row_atk_down, frame_count=frame_count, scale_factor=0.5
            )
            animations["atk_up"] = self.asset_loader.load_grid_row(
                path, row_index=row_atk_up, frame_count=frame_count, scale_factor=0.5
            )
            return animations

        except Exception as e:
            print(f"Error loading unit assets from {path}: {e}")
            return animations

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
        castle_destroyed_image = self.asset_loader.load_image(
            self.asset_loader.paths.castle_destroyed,
            scale_factor=settings.default_sprite_scale,
        )

        return castle_blue_image, castle_red_image, castle_destroyed_image

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
                    scale_factor=1.0,  # Adjust scale if dust is too big/small
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
                    scale_factor=1.0,
                )
            except Exception:
                print("Failed to load Explosion")

        # Fallback if loading failed
        if not frames:
            s = pygame.Surface((20, 20))
            s.fill((255, 255, 0))  # Yellow square fallback
            frames = [s]

        return frames
