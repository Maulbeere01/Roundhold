"""Central render manager with layer support and Y-sorting."""

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared.game import MAP_WIDTH_TILES, TILE_SIZE_PX, PlayerID
from td_shared.simulation import GameState, SimEntity

from ..sprites.animation import AnimationManager
from ..sprites.buildings import BuildingSprite
from ..sprites.buildings import MannedTowerSprite
from ..sprites.units import UnitSprite
from .foam_renderer import FoamRenderer
from .map_layer_renderer import MapLayerRenderer
from .road_renderer import RoadRenderer
from .sprite_factory import SpriteFactory

logger = logging.getLogger(__name__)

# Type-only imports to avoid circular dependencies at runtime
if TYPE_CHECKING:
    from ..assets.template_manager import TemplateManager
    from ..config import GameSettings
    from ..map.map_renderer import TileMap


class RenderManager:
    """Manages rendering order: maps, paths, Y-sorted sprites

    Coordinates rendering of all game elements in the correct layer order,
    including static maps, animated effects, and Y-sorted sprites
    """

    def __init__(
        self,
        render_surface: pygame.Surface,
        template_manager: "TemplateManager",
        settings: "GameSettings",
        tile_size: int,
        screen_width: int,
        screen_height: int,
        player_id: PlayerID,
    ):
        """Initialize render manager with target surface and common dependencies

        Args:
            render_surface: Surface to render all elements onto
            template_manager: TemplateManager instance for assets/templates
            settings: GameSettings instance
            tile_size: Size of tiles in pixels
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            player_id: The ID of the local player ("A" or "B")
        """
        self.render_surface = render_surface
        self.template_manager = template_manager
        self.settings = settings
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height
        self._player_id = player_id

        # Sprite groups for Y-sorted rendering
        self.buildings = pygame.sprite.Group()
        self.units = pygame.sprite.Group()
        self.decor = pygame.sprite.Group()
        self.effects = pygame.sprite.Group()

        # Central animation manager
        self.animation_manager = AnimationManager()

        # Services
        self.map_layer_renderer = MapLayerRenderer(
            self.animation_manager, self.template_manager
        )
        self.sprite_factory = SpriteFactory(
            self.template_manager, self.animation_manager
        )
        self.sprite_factory.configure_groups(self.units, self.buildings, self.effects)
        self.unit_sprites: dict[int, UnitSprite] = self.sprite_factory.unit_sprites
        self.tower_sprites: dict[int, BuildingSprite] = (
            self.sprite_factory.tower_sprites
        )

        self.road_renderer: RoadRenderer | None = None
        self.foam_renderer: FoamRenderer | None = None

        self.map_width_px = MAP_WIDTH_TILES * TILE_SIZE_PX

    def set_map(self, terrain_map: "TileMap"):
        """Set the map instance for coordinate translation."""
        self.terrain_map = terrain_map
        self.map_width_px = int(self.terrain_map.image.get_width())
        self.map_layer_renderer.configure(
            self.tile_size, self.screen_width, self.screen_height
        )
        self.sprite_factory.configure_groups(self.units, self.buildings, self.effects)

    def initialize(self, game) -> None:
        """Initialize all rendering components with game state.

        Centralizes the initialization of all rendering subsystems:
        - Map setup
        - Water background
        - Environment effects (foam, paths)
        - Sprite templates

        Args:
            game: GameSimulation instance providing terrain_map, settings, map dimensions, etc.
        """
        self.set_map(game.terrain_map)
        self.initialize_water_background()
        self.initialize_environment_effects(
            game.terrain_map,
            game.settings.vertical_offset,
            game.map_state.map_width,
            game.map_state.center_x,
        )

        self.initialize_sprites(
            game.map_state.center_x,
            game.map_state.center_y,
            game.map_state.map_width,
            game.settings.vertical_offset,
        )

    def _get_tilemap(self):
        return self.terrain_map

    def initialize_water_background(self) -> None:
        """Initialize water tile background layer

        Loads the water tile from the separate Water.png file and scales it
        to match the tile size for tiling across the screen.
        """

        self.map_layer_renderer.initialize_water()
        logger.debug("Water background initialized")

    def initialize_environment_effects(
        self, terrain_map: "TileMap", map_offset_y: int, map_width: int, center_x: int
    ) -> None:
        """Initialize environment effects (foam, paths, etc.).

        Centralizes the initialization of all environment rendering effects

        Args:
            terrain_map: Single TileMap instance
            map_offset_y: Vertical offset of map
            map_width: Width of map in pixels
            center_x: Center X coordinate of screen
        """

        self._initialize_foam(terrain_map, map_offset_y)
        self._initialize_paths(map_width, center_x, map_offset_y)
        # Pass road_renderer to map_layer_renderer so it can draw paths
        self.map_layer_renderer.set_road_renderer(self.road_renderer)

    def _initialize_foam(self, terrain_map: "TileMap", map_offset_y: int) -> None:
        """Initialize foam renderer for water animation

        Args:
            terrain_map: Single TileMap instance
            map_offset_y: Vertical offset of map
        """
        from ..map import FOAM_TILE_POSITIONS

        foam_frames = self.template_manager.get_foam_frames(
            frame_count=FoamRenderer.FOAM_FRAMES
        )

        # Convert tile coordinates to pixel positions
        foam_positions = []

        for row, col in FOAM_TILE_POSITIONS:
            x = terrain_map.rect.x + col * self.tile_size
            y = map_offset_y + row * self.tile_size
            # Mark left island (cols 0-21) as True, right island (cols 24-45) as False
            is_left_island = col <= 21
            foam_positions.append((x, y, is_left_island))

        self.foam_renderer = FoamRenderer(
            foam_frames,
            foam_positions,
            self.tile_size,
            self.screen_width,
            self.screen_height,
        )

        self.map_layer_renderer.initialize_foam(self.foam_renderer)
        logger.debug(f"Foam renderer initialized with {len(foam_positions)} positions")

    def _initialize_paths(
        self, map_width: int, center_x: int, map_offset_y: int
    ) -> None:
        """Initialize path manager for road/path rendering

        Args:
            map_width: Width of map in pixels
            center_x: Center X coordinate of screen
            map_offset_y: Vertical offset of map
        """
        from td_shared.game import GAME_PATHS

        path_tile_image = self.template_manager.get_path_tile_image()
        map_cols = map_width // self.tile_size

        # Get all path positions from both players
        path_positions = []
        for player_id in ["A", "B"]:
            for route_paths in GAME_PATHS[player_id].values():
                path_positions.extend(route_paths)

        self.road_renderer = RoadRenderer(
            path_tile_image,
            self.tile_size,
            map_width,
            map_cols,
            center_x - map_width // 2,
            map_offset_y,
            self.screen_width,
            self.screen_height,
        )

        self.road_renderer.set_paths(path_positions)
        logger.debug(f"Road renderer initialized with {len(path_positions)} road tiles")

    def initialize_sprites(
        self, center_x: int, center_y: int, map_width: int, vertical_offset: int
    ) -> None:
        """Initialize sprite asset templates.

        Loads asset templates for dynamically creating sprites based on simulation state.

        Args:
            center_x: Center X coordinate of screen
            center_y: Center Y coordinate of screen
            map_width: Width of map in pixels
            vertical_offset: Vertical offset of map
        """

        self.template_manager.preload_templates()
        self._create_static_castles(center_x, center_y, map_width)
        logger.debug("Sprite templates loaded")

    def _sim_to_screen_pos(self, entity: SimEntity) -> pygame.Vector2:
        """Translate a simulation coordinate to a screen coordinate.

        The server sends authoritative global pixel coordinates,
        so we simply add the map offset.
        """

        if self.terrain_map is None:
            return pygame.Vector2(entity.x, entity.y)
        return pygame.Vector2(
            entity.x + self.terrain_map.rect.x, entity.y + self.terrain_map.rect.y
        )

    def sync_sprites_to_state(self, game_state: GameState, ui_state=None) -> None:
        """Synchronize sprite positions and state with simulation.

        This is the core method that bridges the simulation and rendering:
        - Translates local simulation coordinates to global screen coordinates
        - Creates new sprites for new simulation entities
        - Updates positions of existing sprites from simulation state
        - Removes sprites for inactive simulation entities

        Args:
            game_state: Current simulation state
            ui_state: Optional UI state for preview sprite management
        """

        # Track which units we've seen spawn to remove their preview sprites
        if not hasattr(self, '_spawned_unit_ids'):
            self._spawned_unit_ids = set()
        
        # Sync units
        for unit in game_state.units:
            entity_id = unit.entity_id

            # Check if unit is active
            if not unit.is_active:
                # Remove sprite if it exists
                if entity_id in self.unit_sprites:
                    self.sprite_factory.remove_unit_sprite(entity_id)
                    logger.debug(f"Removed inactive unit sprite {entity_id}")
                continue
            
            # When a unit first spawns (becomes active), remove its corresponding preview sprite
            # Since units spawn in order, we remove the first preview for this route/player
            if entity_id not in self._spawned_unit_ids:
                self._spawned_unit_ids.add(entity_id)
                
                if ui_state is not None and hasattr(ui_state, 'route_preview_sprites'):
                    # Find the first preview sprite matching this unit's route and player
                    for sprite in list(ui_state.route_preview_sprites):
                        if (hasattr(sprite, '_preview_route') and 
                            hasattr(sprite, '_preview_player') and
                            sprite._preview_route == unit.route and
                            sprite._preview_player == unit.player_id):
                            sprite.kill()
                            self.animation_manager.unregister(sprite)
                            ui_state.route_preview_sprites.remove(sprite)
                            logger.debug(f"Removed preview sprite for spawning unit {entity_id} (route {unit.route})")
                            break

            # Translate local simulation coordinates to global screen coordinates
            render_pos = self._sim_to_screen_pos(unit)

            if entity_id not in self.unit_sprites:
                sprite = self.sprite_factory.create_unit_sprite(
                    entity_id=entity_id,
                    unit_type=unit.unit_type,
                    player_id=unit.player_id,
                    x=render_pos.x,
                    y=render_pos.y,
                )
                if hasattr(sprite, "update_health"):
                    sprite.update_health(unit.health, unit.max_health, ui_state)
                    
                logger.debug(
                    f"Created unit sprite {entity_id} (player={unit.player_id}) at ({render_pos.x}, {render_pos.y})"
                )
            else:
                # Update existing sprite position
                sprite = self.unit_sprites[entity_id]
                sprite.set_position(render_pos.x, render_pos.y)
                if hasattr(sprite, "update_health"):
                    sprite.update_health(unit.health, unit.max_health, ui_state)

        # Sync towers
        for tower in game_state.towers:
            # --- HANDLE BASE DEFENSE TOWERS ---
            if tower.tower_type == "castle_archer":
                # Don't create a sprite, find the existing castle
                target_sprite = self.castle_A_sprite if tower.player_id == "A" else self.castle_B_sprite
                
                # Update aiming based on ACTUAL simulation target
                if hasattr(target_sprite, "update_facing"):
                    if tower.last_shot_target:
                        class Dummy: pass
                        d = Dummy()
                        d.x, d.y = tower.last_shot_target
                        target_screen_pos = self._sim_to_screen_pos(d)
                        target_sprite.update_facing(target_screen_pos.x, target_screen_pos.y)
                    else:
                        target_sprite.reset_to_idle()
                continue
            
            entity_id = tower.entity_id

            # Check if tower is active
            if not tower.is_active:
                # Remove sprite if it exists
                if entity_id in self.tower_sprites:
                    self.sprite_factory.remove_tower_sprite(entity_id)
                    logger.debug(f"Removed inactive tower sprite {entity_id}")
                continue

            # Translate local simulation coordinates to global screen coordinates
            render_pos = self._sim_to_screen_pos(tower)

            if entity_id not in self.tower_sprites:
                # --- UPDATE: Pass tower.player_id ---
                sprite = self.sprite_factory.create_tower_sprite(
                    entity_id=entity_id,
                    tower_type=tower.tower_type,
                    player_id=tower.player_id,
                    x=render_pos.x,
                    y=render_pos.y,
                    range_px=tower.range_px,
                )
            else:
                sprite = self.tower_sprites[entity_id]
            if isinstance(sprite, MannedTowerSprite):
                # Check if the sim tower has a target
                if tower.last_shot_target:
                    # Convert sim target pos to screen pos
                    # We create a dummy object to use _sim_to_screen_pos
                    class Dummy: pass
                    d = Dummy()
                    d.x, d.y = tower.last_shot_target
                    
                    target_screen_pos = self._sim_to_screen_pos(d)
                    sprite.update_facing(target_screen_pos.x, target_screen_pos.y)
                else:
                    sprite.reset_to_idle()

        self._update_castle_aiming(game_state)

    def _update_castle_aiming(self, game_state: GameState) -> None:
        """Update castle archer facing based on the actual castle tower shot target."""

        def get_castle_tower(player_id: str):
            for tower in game_state.towers:
                if tower.tower_type == "castle_archer" and tower.player_id == player_id:
                    return tower
            return None

        def update_single_castle(castle_sprite, player_id: str):
            if not getattr(castle_sprite, "archer_alive", False):
                return

            tower = get_castle_tower(player_id)
            if tower and tower.last_shot_target and tower.shoot_anim_timer > 0:
                # Use the authoritative target from the sim to avoid jitter when units are far
                class Dummy: pass
                d = Dummy()
                d.x, d.y = tower.last_shot_target
                target_screen_pos = self._sim_to_screen_pos(d)
                castle_sprite.update_facing(target_screen_pos.x, target_screen_pos.y)
            else:
                castle_sprite.reset_to_idle()

        if hasattr(self, 'castle_A_sprite'):
            update_single_castle(self.castle_A_sprite, "A")
        if hasattr(self, 'castle_B_sprite'):
            update_single_castle(self.castle_B_sprite, "B")

    def _create_static_castles(
        self, center_x: int, center_y: int, map_width: int
    ) -> None:
        """Create static castle sprites for each player."""

        (
            castle_blue_image,
            castle_red_image,
            self.castle_destroyed_image,
        ) = self.template_manager.get_castle_images(self.settings)

        # Fetch Archer Animations
        archer_anims_A = self.template_manager.get_unit_template("archer", "A")
        archer_anims_B = self.template_manager.get_unit_template("archer", "B")

        # Create Castles as MannedTowerSprite
        # Player A castle (Blue/Left)
        self.castle_A_sprite = MannedTowerSprite(
            x=center_x - map_width // 2 + 100,
            y=center_y,
            image=castle_blue_image,
            archer_anims=archer_anims_A,
            player_id="A",
            archer_offset_y=-50 # Higher offset for castle (adjust if needed)
        )
        
        # Player B castle (Red/Right)
        self.castle_B_sprite = MannedTowerSprite(
            x=center_x + map_width // 2 - 100,
            y=center_y,
            image=castle_red_image,
            archer_anims=archer_anims_B,
            player_id="B",
            archer_offset_y=-50
        )

        # Add to groups
        self.buildings.add(self.castle_A_sprite)
        self.buildings.add(self.castle_B_sprite)
        
        # Register animations so they idle/breathe
        self.animation_manager.register(self.castle_A_sprite)
        self.animation_manager.register(self.castle_B_sprite)

    def destroy_castle(self, player_id: str) -> None:
        """Swaps the castle sprite to the destroyed version and kills archer."""
        target_sprite = (
            self.castle_A_sprite if player_id == "A" else self.castle_B_sprite
        )

        # Only update if it hasn't been destroyed yet
        if target_sprite.image != self.castle_destroyed_image:
            # Trigger visual effect
            if isinstance(target_sprite, MannedTowerSprite):
                archer_pos = target_sprite.kill_archer()
                if archer_pos:
                    # Spawn dust/explosion at archer position
                    self.sprite_factory.create_effect(archer_pos[0], archer_pos[1], "spawn_dust")
            
            # Swap Image
            old_midbottom = target_sprite.rect.midbottom
            target_sprite.image = self.castle_destroyed_image
            target_sprite.rect = target_sprite.image.get_rect(midbottom=old_midbottom)
            
            # Stop animating this castle
            self.animation_manager.unregister(target_sprite)
            
            logger.info(f"Visuals: Castle {player_id} destroyed.")
        """Swaps the castle sprite to the destroyed version."""
        target_sprite = (
            self.castle_A_sprite if player_id == "A" else self.castle_B_sprite
        )

        # Only update if it hasn't been destroyed yet
        if target_sprite.image != self.castle_destroyed_image:
            old_midbottom = target_sprite.rect.midbottom
            target_sprite.image = self.castle_destroyed_image
            # Re-set rect to ensure it stays centered on the ground
            target_sprite.rect = target_sprite.image.get_rect(midbottom=old_midbottom)
            logger.info(f"Visuals: Castle {player_id} destroyed.")

    def _draw_water_background(self) -> None:
        """Draw water tile background layer (lowest layer)."""
        self.map_layer_renderer.draw_background(self.render_surface)

    def _draw_elevation(self, tile_map) -> None:
        """Draw elevation/cliff layer for a tilemap.

        Args:
            tile_map: TileMap instance
        """

        elevation = tile_map.get_elevation_surface()
        elev_offset = tile_map.get_elevation_offset()
        self.render_surface.blit(
            elevation,
            (tile_map.rect.x + elev_offset[0], tile_map.rect.y + elev_offset[1]),
        )

    def _draw_foam(self) -> None:
        """Draw animated foam layer."""
        self.map_layer_renderer.draw_foam(self.render_surface)

    def _draw_paths(self) -> None:
        """Draw road overlay layer"""
        self.map_layer_renderer.draw_paths(self.render_surface)

    def _draw_tower_ranges(self) -> None:
        """Draw translucent range indicators for towers."""
        for sprite in self.buildings:
            overlay = sprite.get_range_overlay()
            if overlay:
                surface, rect = overlay
                self.render_surface.blit(surface, rect)

    def _draw_sorted_sprites(self) -> None:
        all_sprites = list(self.buildings) + list(self.units) + list(self.decor) + list(self.effects)
        sorted_sprites = sorted(all_sprites, key=lambda s: s.get_sort_key())
        for sprite in sorted_sprites:
            if hasattr(sprite, "draw_on"):
                sprite.draw_on(self.render_surface)
            else:
                self.render_surface.blit(sprite.image, sprite.rect)

    def draw(self, terrain_map) -> None:
        """Render everything in correct layered order.

        Rendering order:
        1. Water background (water tiles)
        2. Foam (water-land boundaries)
        3. Elevation/cliff walls
        4. Map tiles
        5. Paths
        6. Y-sorted sprites

        Args:
            terrain_map: Single TileMap instance
        """
        self._draw_water_background()
        self._draw_foam()

        self._draw_elevation(terrain_map)

        self.render_surface.blit(terrain_map.image, terrain_map.rect)

        self._draw_paths()
        self._draw_tower_ranges()
        self._draw_sorted_sprites()

    def update(self, dt: float):
        """Update dynamic sprites and animations.

        Args:
            dt: Delta time in seconds since last frame
        """
        # Update all animations centrally
        self.animation_manager.update_all(dt)

        # Update sprite-specific logic (e.g., movement for units)
        self.units.update(dt)
        
        # Update buildings (for hit flash effects)
        self.buildings.update(dt)
        
        # Also update castle sprites directly if they exist
        if hasattr(self, 'castle_A_sprite') and self.castle_A_sprite:
            self.castle_A_sprite.update(dt)
        if hasattr(self, 'castle_B_sprite') and self.castle_B_sprite:
            self.castle_B_sprite.update(dt)
