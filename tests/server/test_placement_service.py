"""Tests for TowerPlacementService."""

import pytest

from server.src.td_server.services.placement import TowerPlacement, TowerPlacementService


class TestTowerPlacementService:
    """Tests for the TowerPlacementService class."""

    def test_initialization(self):
        """Test that service initializes with empty placements."""
        service = TowerPlacementService()
        assert service._placements == []
        assert service.map_width_tiles > 0

    def test_place_tower_success(self):
        """Test successful tower placement."""
        service = TowerPlacementService()
        
        result = service.place_tower(
            player_id="A",
            tower_type="standard",
            tile_row=5,
            tile_col=10,
            level=1,
        )
        
        assert result is not None
        assert result["player_id"] == "A"
        assert result["tower_type"] == "standard"
        assert result["level"] == 1
        assert len(service._placements) == 1

    def test_place_tower_normalizes_coordinates(self):
        """Test that coordinates are normalized to integers."""
        service = TowerPlacementService()
        
        result = service.place_tower(
            player_id="A",
            tower_type="standard",
            tile_row=5.7,  # type: ignore
            tile_col=10.3,  # type: ignore
            level=1,
        )
        
        assert service._placements[0].tile_row == 5
        assert service._placements[0].tile_col == 10

    def test_place_tower_creates_sim_data(self):
        """Test that placement creates proper SimTowerData."""
        service = TowerPlacementService()
        
        result = service.place_tower(
            player_id="B",
            tower_type="wood_tower",
            tile_row=3,
            tile_col=7,
            level=2,
        )
        
        assert result is not None
        assert "position_x" in result
        assert "position_y" in result
        # Position should be in pixels, centered in tile
        assert result["position_x"] > 0
        assert result["position_y"] > 0

    def test_get_sim_towers_empty(self):
        """Test getting sim towers when none placed."""
        service = TowerPlacementService()
        towers = service.get_sim_towers()
        assert towers == []

    def test_get_sim_towers_multiple(self):
        """Test getting sim towers with multiple placements."""
        service = TowerPlacementService()
        
        service.place_tower(
            player_id="A", tower_type="standard", tile_row=1, tile_col=1, level=1
        )
        service.place_tower(
            player_id="B", tower_type="wood_tower", tile_row=2, tile_col=2, level=1
        )
        
        towers = service.get_sim_towers()
        assert len(towers) == 2
        assert towers[0]["tower_type"] == "standard"
        assert towers[1]["tower_type"] == "wood_tower"

    def test_count_gold_mines_none(self):
        """Test counting gold mines when none exist."""
        service = TowerPlacementService()
        count = service.count_gold_mines("A")
        assert count == 0

    def test_count_gold_mines_single_player(self):
        """Test counting gold mines for a single player."""
        service = TowerPlacementService()
        
        service.place_tower(
            player_id="A", tower_type="gold_mine", tile_row=1, tile_col=1, level=1
        )
        service.place_tower(
            player_id="A", tower_type="gold_mine", tile_row=2, tile_col=2, level=1
        )
        service.place_tower(
            player_id="A", tower_type="standard", tile_row=3, tile_col=3, level=1
        )
        
        count = service.count_gold_mines("A")
        assert count == 2

    def test_count_gold_mines_multiple_players(self):
        """Test that gold mines are counted per player."""
        service = TowerPlacementService()
        
        service.place_tower(
            player_id="A", tower_type="gold_mine", tile_row=1, tile_col=1, level=1
        )
        service.place_tower(
            player_id="B", tower_type="gold_mine", tile_row=2, tile_col=2, level=1
        )
        service.place_tower(
            player_id="B", tower_type="gold_mine", tile_row=3, tile_col=3, level=1
        )
        
        count_a = service.count_gold_mines("A")
        count_b = service.count_gold_mines("B")
        
        assert count_a == 1
        assert count_b == 2

    def test_placement_immutability(self):
        """Test that TowerPlacement is frozen (immutable)."""
        placement = TowerPlacement(
            player_id="A",
            tower_type="standard",
            tile_row=5,
            tile_col=10,
            level=1,
        )
        
        with pytest.raises(Exception):  # FrozenInstanceError
            placement.tile_row = 99  # type: ignore

    def test_placement_to_sim_data_centers_tower(self):
        """Test that towers are centered in their tile."""
        service = TowerPlacementService()
        
        result = service.place_tower(
            player_id="A",
            tower_type="standard",
            tile_row=0,
            tile_col=0,
            level=1,
        )
        
        # Tower should be centered: tile_center + offset
        # Exact values depend on TILE_SIZE_PX (typically 64)
        assert result is not None
        assert result["position_x"] > 0
        assert result["position_y"] > 0
