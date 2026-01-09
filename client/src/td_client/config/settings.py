"""Game settings and configuration constants."""

from dataclasses import dataclass

from td_shared.game import TILE_SIZE_PX

# Tile configuration (source and rendering)
TILE_SOURCE_SIZE = 64  # Dont change

# Screen dimensions (base render resolution)
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


@dataclass
class GameSettings:
    """Centralized game configuration.

    This class holds all tunable game parameters including display settings,
    rendering options, and debug visualization controls.
    """

    # Display settings
    fps: int = 60

    # Tile settings
    tile_size: int = TILE_SIZE_PX
    vertical_offset: int = TILE_SIZE_PX  # Vertical positioning offset for maps

    # Debug
    show_grid: bool = False  # Display debug grid overlay on startup
    show_grid_coords: bool = True  # Show row,col coordinates in grid cells
    grid_color: tuple = (255, 255, 255, 100)  # RGBA color for grid lines
    grid_thickness: int = 1  # Grid line thickness in pixels

    # Sprite settings
    default_sprite_scale: float = 0.5  # Default scale factor for sprite assets
