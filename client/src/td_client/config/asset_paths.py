"""Asset path management."""

import os
from pathlib import Path


class AssetPaths:
    """Centralized asset path manager for all game resources."""

    def __init__(self):
        """Initialize asset paths relative to project structure"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = Path(base_dir)
        self.assets_dir = self.base_dir.parent.parent / "assets"

        self.terrain_dir = self.assets_dir / "Terrain" / "Ground"
        self.tileset_flat = self.terrain_dir / "Tilemap_Flat.png"
        self.tileset_elevation = self.terrain_dir / "Tilemap_Elevation.png"

        self.water_dir = self.assets_dir / "Terrain" / "Water"
        self.water = self.water_dir / "Water.png"
        self.foam = self.water_dir / "Foam" / "Foam.png"

        self.buildings_dir = (
            self.assets_dir / "Factions" / "Knights" / "Buildings" / "Castle"
        )
        self.castle_blue = self.buildings_dir / "Castle_Blue.png"
        self.castle_red = self.buildings_dir / "Castle_Red.png"
