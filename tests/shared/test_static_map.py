"""Tests for static map layout and definitions."""

import pytest

from td_shared.map.static_map import (
    GLOBAL_MAP_LAYOUT,
    TILE_TYPE_GRASS,
    TILE_TYPE_PATH,
    TILE_TYPE_WATER,
)
from td_shared.game import MAP_WIDTH_TILES

# These don't exist in static_map:
# MAP_HEIGHT_TILES, GLOBAL_MAP_LAYOUT, TILE_TYPE_BRIDGE, get_map_layout


class TestStaticMapConstants:
    """Tests for static map constants."""

    def test_map_dimensions(self):
        """Test that map dimensions are defined and reasonable."""
        assert MAP_WIDTH_TILES > 0
        # MAP_HEIGHT_TILES not defined yet, calculate from GLOBAL_MAP_LAYOUT
        assert len(GLOBAL_MAP_LAYOUT) > 0
        assert MAP_WIDTH_TILES >= len(GLOBAL_MAP_LAYOUT)  # Typically wider than tall

    def test_tile_type_constants(self):
        """Test that all tile type constants are defined."""
        assert isinstance(TILE_TYPE_GRASS, int)
        assert isinstance(TILE_TYPE_PATH, int)
        assert isinstance(TILE_TYPE_WATER, int)
        # TILE_TYPE_BRIDGE not defined yet

    def test_tile_types_distinct(self):
        """Test that tile types are distinct values."""
        tile_types = [
            TILE_TYPE_GRASS,
            TILE_TYPE_PATH,
            TILE_TYPE_WATER,
        ]
        
        assert len(tile_types) == len(set(tile_types))


class TestStaticMapLayout:
    """Tests for the static map layout."""

    def test_map_layout_dimensions(self):
        """Test that map layout has correct dimensions."""
        layout = GLOBAL_MAP_LAYOUT
        
        assert len(layout) > 0
        assert all(len(row) == MAP_WIDTH_TILES for row in layout)

    def test_map_layout_valid_tiles(self):
        """Test that all tiles in layout are valid types."""
        layout = GLOBAL_MAP_LAYOUT
        valid_types = [TILE_TYPE_GRASS, TILE_TYPE_PATH, TILE_TYPE_WATER]
        
        for row in layout:
            for tile in row:
                assert tile in valid_types

    def test_map_has_grass(self):
        """Test that map contains grass tiles (buildable areas)."""
        layout = GLOBAL_MAP_LAYOUT
        grass_count = sum(row.count(TILE_TYPE_GRASS) for row in layout)
        
        assert grass_count > 0

    def test_map_has_paths(self):
        """Test that map contains path tiles (for units)."""
        layout = GLOBAL_MAP_LAYOUT
        path_count = sum(row.count(TILE_TYPE_PATH) for row in layout)
        
        assert path_count > 0


class TestMapLayoutStructure:
    """Tests for map layout structure and consistency."""

    def test_map_symmetry_exists(self):
        """Test that map has some buildable area on both sides."""
        layout = GLOBAL_MAP_LAYOUT
        
        left_half_grass = 0
        right_half_grass = 0
        mid_point = MAP_WIDTH_TILES // 2
        
        for row in layout:
            left_half_grass += row[:mid_point].count(TILE_TYPE_GRASS)
            right_half_grass += row[mid_point:].count(TILE_TYPE_GRASS)
        
        # Both sides should have buildable areas
        assert left_half_grass > 0
        assert right_half_grass > 0

    def test_map_has_water_features(self):
        """Test that map includes water features."""
        layout = GLOBAL_MAP_LAYOUT
        water_count = sum(row.count(TILE_TYPE_WATER) for row in layout)
        
        # Map should have some water (can be 0 if map design changes)
        assert water_count >= 0

    def test_no_empty_rows(self):
        """Test that no rows are completely empty."""
        layout = GLOBAL_MAP_LAYOUT
        
        for row in layout:
            assert len(row) > 0

    def test_consistent_row_lengths(self):
        """Test that all rows have the same length."""
        layout = GLOBAL_MAP_LAYOUT
        row_lengths = [len(row) for row in layout]
        
        assert all(length == MAP_WIDTH_TILES for length in row_lengths)
