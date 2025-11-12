"""Central render manager with layer support and Y-sorting."""
import logging
from typing import TYPE_CHECKING, Dict, List, Optional

import pygame

from ..sprites.animation import AnimationManager
from ..sprites.buildings import BuildingSprite
from ..sprites.units import UnitSprite
from .foam_renderer import FoamRenderer
from .road_renderer import RoadRenderer
from .coordinate_translator import CoordinateTranslator
from .map_layer_renderer import MapLayerRenderer
from .sprite_factory import SpriteFactory
from td_shared.simulation import GameState, SimEntity
from td_shared.game import MAP_WIDTH_TILES, TILE_SIZE_PX, PlayerID

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
        self.coord_translator = CoordinateTranslator(self._get_tilemaps)
        self.map_layer_renderer = MapLayerRenderer(self.animation_manager, self.template_manager)
        self.sprite_factory = SpriteFactory(self.template_manager, self.animation_manager)
        self.sprite_factory.configure_groups(self.units, self.buildings)
        self.unit_sprites: Dict[int, UnitSprite] = self.sprite_factory.unit_sprites
        self.tower_sprites: Dict[int, BuildingSprite] = self.sprite_factory.tower_sprites

        self.road_renderer: Optional[RoadRenderer] = None
        self.foam_renderer: Optional[FoamRenderer] = None

        self.left_map: Optional["TileMap"] = None
        self.right_map: Optional["TileMap"] = None
        self.map_width_px = MAP_WIDTH_TILES * TILE_SIZE_PX


    def set_maps(self, left_map: "TileMap", right_map: "TileMap"):
        """Set the map instances for coordinate translation."""
        self.left_map = left_map
        self.right_map = right_map
        # Derive actual map width in pixels to avoid drift from theoretical constants
        try:
            self.map_width_px = int(self.left_map.image.get_width())
        except Exception:
            # Fallback to shared constant
            self.map_width_px = MAP_WIDTH_TILES * TILE_SIZE_PX
        self.coord_translator.set_map_width(self.map_width_px)
        self.map_layer_renderer.configure(self.tile_size, self.screen_width, self.screen_height)
        self.sprite_factory.configure_groups(self.units, self.buildings)

    def _get_tilemaps(self):
        return self.left_map, self.right_map

    def initialize_water_background(self) -> None:
        """Initialize water tile background layer
        
        Loads the water tile from the separate Water.png file and scales it
        to match the tile size for tiling across the screen.
        """
        self.map_layer_renderer.initialize_water()
        logger.debug("Water background initialized")
    
    def initialize_environment_effects(
        self,
        left_map: "TileMap",
        right_map: "TileMap",
        map_offset_y: int,
        left_map_width: int,
        center_x: int
    ) -> None:
        """Initialize environment effects (foam, paths, etc.).
        
        Centralizes the initialization of all environment rendering effects
        
        Args:
            left_map: Left TileMap instance
            right_map: Right TileMap instance
            map_offset_y: Vertical offset of maps
            left_map_width: Width of left map in pixels
            center_x: Center X coordinate of screen
        """
        self._initialize_foam(
            left_map, right_map, map_offset_y
        )
        self._initialize_paths(
            left_map_width, center_x, map_offset_y
        )
        # Pass road_renderer to map_layer_renderer so it can draw paths
        if self.road_renderer:
            self.map_layer_renderer.set_road_renderer(self.road_renderer)
    
    def _initialize_foam(
        self,
        left_map: "TileMap",
        right_map: "TileMap",
        map_offset_y: int
    ) -> None:
        """Initialize foam renderer for water animation
        
        Args:
            left_map: Left TileMap instance
            right_map: Right TileMap instance
            map_offset_y: Vertical offset of maps
        """
        from ..map import FOAM_TILE_POSITIONS
        
        foam_frames = self.template_manager.get_foam_frames(
            frame_count=FoamRenderer.FOAM_FRAMES
        )
        
        # Convert tile coordinates to pixel positions
        # Same positions are used for both left and right maps
        foam_positions = []
        
        for row, col in FOAM_TILE_POSITIONS:
            # Left map position
            x_left = left_map.rect.x + col * self.tile_size
            y = map_offset_y + row * self.tile_size
            foam_positions.append((x_left, y, True))
            
            # Right map position (same tile coordinates)
            x_right = right_map.rect.x + col * self.tile_size
            foam_positions.append((x_right, y, False))
        
        self.foam_renderer = FoamRenderer(
            foam_frames,
            foam_positions,
            self.tile_size,
            self.screen_width,
            self.screen_height
        )
        self.map_layer_renderer.initialize_foam(self.foam_renderer)
        logger.debug(f"Foam renderer initialized with {len(foam_positions)} positions")
    
    def _initialize_paths(
        self,
        left_map_width: int,
        center_x: int,
        map_offset_y: int
    ) -> None:
        """Initialize path manager for road/path rendering
        
        Args:
            left_map_width: Width of left map in pixels
            center_x: Center X coordinate of screen
            map_offset_y: Vertical offset of maps
        """
        from ..map import LEFT_PATH_POSITIONS
        
        path_tile_image = self.template_manager.get_path_tile_image()
        left_map_cols = left_map_width // self.tile_size
        
        self.road_renderer = RoadRenderer(
            path_tile_image,
            self.tile_size,
            left_map_width,
            left_map_cols,
            center_x - left_map_width,
            map_offset_y,
            self.screen_width,
            self.screen_height
        )
        
        right_path_positions = self.road_renderer.mirror_paths(
            LEFT_PATH_POSITIONS
        )
        path_positions = LEFT_PATH_POSITIONS + right_path_positions
        self.road_renderer.set_paths(path_positions)
        logger.debug(
            f"Road renderer initialized with {len(path_positions)} road tiles"
        )
    
    def initialize_sprites(
        self,
        center_x: int,
        center_y: int,
        left_map_width: int,
        vertical_offset: int
    ) -> None:
        """Initialize sprite asset templates.
        
        Loads asset templates for dynamically creating sprites based on simulation state.
        
        Args:
            center_x: Center X coordinate of screen
            center_y: Center Y coordinate of screen
            left_map_width: Width of left map in pixels
            vertical_offset: Vertical offset of maps
        """
        self.template_manager.preload_templates()
        self._create_static_castles(center_x, center_y, left_map_width)
        logger.debug("Sprite templates loaded")

    def _sim_to_screen_pos(self, entity: SimEntity) -> pygame.Vector2:
        """Translate a simulation coordinate to a screen coordinate."""
        is_tower = hasattr(entity, "tower_type")
        return self.coord_translator.sim_to_screen(entity, is_tower=is_tower)

    def sync_sprites_to_state(self, game_state: GameState) -> None:
        """Synchronize sprite positions and state with simulation.
        
        This is the core method that bridges the simulation and rendering:
        - Translates local simulation coordinates to global screen coordinates
        - Creates new sprites for new simulation entities
        - Updates positions of existing sprites from simulation state
        - Removes sprites for inactive simulation entities
        
        Args:
            game_state: Current simulation state
        """
        if not self.left_map or not self.right_map:
            logger.warning("Maps not set in RenderManager, cannot sync sprites.")
            return

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
                logger.debug(f"Created unit sprite {entity_id} (player={unit.player_id}) at ({render_pos.x}, {render_pos.y})")
            else:
                # Update existing sprite position
                sprite = self.unit_sprites[entity_id]
                sprite.set_position(render_pos.x, render_pos.y)
        
        # Sync towers
        for tower in game_state.towers:
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
                sprite = self.sprite_factory.create_tower_sprite(
                    entity_id=entity_id,
                    tower_type=tower.tower_type,
                    x=render_pos.x,
                    y=render_pos.y,
                    range_px=tower.range_px,
                )
                if sprite:
                    logger.debug(f"Created tower sprite {entity_id} at ({render_pos.x}, {render_pos.y})")
                else:
                    logger.warning(f"No template for tower type: {tower.tower_type}")
            else:
                sprite = self.tower_sprites[entity_id]
                sprite.set_position(render_pos.x, render_pos.y)

    def _create_static_castles(
        self,
        center_x: int,
        center_y: int,
        left_map_width: int
    ) -> None:
        """Create static castle sprites for each player."""
        castle_blue_image, castle_red_image = self.template_manager.get_castle_images(self.settings)

        castle_blue = BuildingSprite(
            center_x - left_map_width + self.tile_size * 1.5,
            center_y,
            castle_blue_image,
        )
        castle_red = BuildingSprite(
            center_x + left_map_width - self.tile_size * 1.5,
            center_y,
            castle_red_image,
        )

        self.buildings.add(castle_blue)
        self.buildings.add(castle_red)
    
    def _draw_water_background(self) -> None:
        """Draw water tile background layer (lowest layer)."""
        self.map_layer_renderer.draw_background(self.render_surface)
    
    def _draw_foam(self) -> None:
        """Draw animated foam layer."""
        self.map_layer_renderer.draw_foam(self.render_surface)
    
    def _draw_elevation(self, tile_map) -> None:
        """Draw elevation/cliff layer for a tilemap.
        
        Args:
            tile_map: TileMap instance
        """
        elevation = tile_map.get_elevation_surface()
        if elevation:
            elev_offset = tile_map.get_elevation_offset()
            self.render_surface.blit(
                elevation,
                (
                    tile_map.rect.x + elev_offset[0],
                    tile_map.rect.y + elev_offset[1]
                )
            )
    
    def _draw_paths(self) -> None:
        """Draw road overlay layer"""
        self.map_layer_renderer.draw_paths(self.render_surface)

    def _draw_tower_ranges(self) -> None:
        """Draw translucent range indicators for towers."""
        for sprite in self.buildings:
            if hasattr(sprite, "get_range_overlay"):
                overlay = sprite.get_range_overlay()
                if overlay:
                    surface, rect = overlay
                    self.render_surface.blit(surface, rect)
    
    def _draw_sorted_sprites(self) -> None:
        """Draw all sprites sorted by Y coordinate"""
        all_sprites = (
            list(self.buildings)
            + list(self.units)
            + list(self.decor)
            + list(self.effects)
        )
        
        sorted_sprites = sorted(
            all_sprites, key=lambda s: s.get_sort_key()
        )
        for sprite in sorted_sprites:
            self.render_surface.blit(sprite.image, sprite.rect)
    
    def draw(self, left_map, right_map) -> None:
        """Render everything in correct layered order.
        
        Rendering order:
        1. Water background (water tiles)
        2. Foam (water-land boundaries)
        3. Elevation/cliff walls
        4. Map tiles
        5. Paths
        6. Y-sorted sprites
        
        Args:
            left_map: Left TileMap instance
            right_map: Right TileMap instance
        """
        self._draw_water_background()
        self._draw_foam()
        
        self._draw_elevation(left_map)
        self._draw_elevation(right_map)
        
        self.render_surface.blit(left_map.image, left_map.rect)
        self.render_surface.blit(right_map.image, right_map.rect)
        
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
