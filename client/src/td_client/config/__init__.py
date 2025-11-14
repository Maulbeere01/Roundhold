"""Configuration modules for the game client."""

from .asset_paths import AssetPaths
from .settings import (
    TILE_SOURCE_SIZE,
    GameSettings,
)

__all__ = [
    "AssetPaths",
    "GameSettings",
    "TILE_SOURCE_SIZE",
]
