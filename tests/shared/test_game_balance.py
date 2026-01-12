"""Tests for game balance constants and calculations."""

import pytest

from td_shared.game import (
    COMBAT_SECONDS,
    DEFAULT_TICK_RATE,
    GOLD_PER_KILL,
    PLAYER_A,
    PLAYER_B,
    PLAYER_LIVES,
    PREP_SECONDS,
    START_GOLD,
    TOWER_STATS,
    UNIT_STATS,
    tile_to_pixel,
)

# pixel_to_tile not implemented yet
# from td_shared.game import pixel_to_tile


class TestGameBalance:
    """Tests for game balance constants."""

    def test_player_constants(self):
        """Test that player constants are defined correctly."""
        assert PLAYER_A == "A"
        assert PLAYER_B == "B"

    def test_economy_constants(self):
        """Test that economy constants are reasonable."""
        assert PLAYER_LIVES > 0
        assert START_GOLD > 0
        assert GOLD_PER_KILL >= 0

    def test_timing_constants(self):
        """Test that timing constants are reasonable."""
        assert DEFAULT_TICK_RATE > 0
        assert PREP_SECONDS > 0
        assert COMBAT_SECONDS > 0
        assert PREP_SECONDS < COMBAT_SECONDS

    def test_unit_stats_all_types_defined(self):
        """Test that all unit types have complete stats."""
        assert "standard" in UNIT_STATS
        assert "pawn" in UNIT_STATS
        assert "archer" in UNIT_STATS
        
        for unit_type, stats in UNIT_STATS.items():
            assert "cost" in stats
            assert "health" in stats
            assert "speed" in stats
            assert "base_damage" in stats
            assert stats["cost"] > 0
            assert stats["health"] > 0
            assert stats["speed"] > 0

    def test_unit_stats_balance(self):
        """Test that unit stats are balanced (expensive = stronger)."""
        standard = UNIT_STATS["standard"]
        pawn = UNIT_STATS["pawn"]
        
        # Pawn costs more, should have more health
        assert pawn["cost"] > standard["cost"]
        assert pawn["health"] > standard["health"]

    def test_tower_stats_all_types_defined(self):
        """Test that all tower types have complete stats."""
        assert "standard" in TOWER_STATS
        assert "wood_tower" in TOWER_STATS
        assert "gold_mine" in TOWER_STATS
        assert "castle_archer" in TOWER_STATS
        
        for tower_type, stats in TOWER_STATS.items():
            assert "cost" in stats
            assert "damage" in stats
            assert "range_px" in stats
            assert "cooldown_ticks" in stats

    def test_tower_stats_combat_towers(self):
        """Test that combat towers have reasonable stats."""
        standard = TOWER_STATS["standard"]
        
        assert standard["cost"] > 0
        assert standard["damage"] > 0
        assert standard["range_px"] > 0
        assert standard["cooldown_ticks"] > 0

    def test_tower_stats_gold_mine(self):
        """Test that gold mine has zero combat stats."""
        gold_mine = TOWER_STATS["gold_mine"]
        
        assert gold_mine["damage"] == 0
        assert gold_mine["range_px"] == 0
        assert gold_mine["cooldown_ticks"] == 0
        assert gold_mine["cost"] > 0

    def test_tower_stats_balance(self):
        """Test that tower stats are balanced (cheap = weaker)."""
        standard = TOWER_STATS["standard"]
        wood = TOWER_STATS["wood_tower"]
        
        # Wood tower is cheaper, should be weaker
        assert wood["cost"] < standard["cost"]
        assert wood["damage"] <= standard["damage"]
        assert wood["range_px"] <= standard["range_px"]


class TestCoordinateConversion:
    """Tests for tile/pixel conversion functions."""

    def test_tile_to_pixel_origin(self):
        """Test tile to pixel conversion at origin."""
        x, y = tile_to_pixel(0, 0)
        assert x == 0
        assert y == 0

    def test_tile_to_pixel_single_tile(self):
        """Test tile to pixel conversion for single tile."""
        x, y = tile_to_pixel(1, 1)
        # Typically TILE_SIZE_PX = 64
        assert x > 0
        assert y > 0
        assert x == y  # Square tiles

    def test_tile_to_pixel_different_coords(self):
        """Test tile to pixel conversion with different row/col."""
        x1, y1 = tile_to_pixel(2, 3)
        x2, y2 = tile_to_pixel(3, 2)
        
        assert x1 != x2
        assert y1 != y2

    def test_tile_to_pixel_scaling(self):
        """Test that tile to pixel scales correctly."""
        x1, y1 = tile_to_pixel(1, 1)
        x2, y2 = tile_to_pixel(2, 2)
        
        # Should be exactly double
        assert x2 == 2 * x1
        assert y2 == 2 * y1
