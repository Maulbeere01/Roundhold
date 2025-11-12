"""Configuration modules for the game client."""

from .paths import AssetPaths
from .settings import (
    GameSettings,
    MAP_HEIGHT_TILES,
    MAP_WIDTH_TILES,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_RENDER_SIZE,
    TILE_SIZE,
    TILE_SOURCE_SIZE,
)

__all__ = [
    'AssetPaths',
    'GameSettings',
    'MAP_HEIGHT_TILES',
    'MAP_WIDTH_TILES',
    'SCREEN_HEIGHT',
    'SCREEN_WIDTH',
    'TILE_RENDER_SIZE',
    'TILE_SIZE',
    'TILE_SOURCE_SIZE',
]
