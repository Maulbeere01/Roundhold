"""Game settings and configuration constants."""
from dataclasses import dataclass
from td_shared.game import TILE_SIZE_PX


# Tile configuration (source and rendering)
TILE_SOURCE_SIZE = 64 # Dont change 
TILE_RENDER_SIZE = TILE_SIZE_PX
TILE_SIZE = TILE_RENDER_SIZE

# Screen dimensions (base render resolution)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080

# Map dimensions calculated to fit screen
MAP_WIDTH_TILES = ((SCREEN_WIDTH // 2) // TILE_RENDER_SIZE) - 2
MAP_HEIGHT_TILES = ((SCREEN_HEIGHT - 2 * TILE_RENDER_SIZE) // TILE_RENDER_SIZE)

@dataclass
class GameSettings:
    """Centralized game configuration.
    
    This class holds all tunable game parameters including display settings,
    rendering options, and debug visualization controls.
    """
    
    # Display settings
    fps: int = 60  
    
    # Tile settings
    tile_size: int = TILE_SIZE  
    tile_render_size: int = TILE_RENDER_SIZE  
    vertical_offset: int = TILE_RENDER_SIZE  # Vertical positioning offset for maps
    
    # Debug
    show_grid: bool = True  # Display debug grid overlay on startup
    show_grid_coords: bool = True  # Show row,col coordinates in grid cells
    grid_color: tuple = (255, 255, 255, 100)  # RGBA color for grid lines
    grid_thickness: int = 1  # Grid line thickness in pixels
    
    # Sprite settings
    default_sprite_scale: float = 0.5  # Default scale factor for sprite assets
