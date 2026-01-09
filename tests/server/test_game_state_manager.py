import pytest

from server.src.td_server.core.game_state_manager import GameStateManager
from server.src.td_server.services import (
    EconomyManager,
    SnapshotBuilder,
    TowerPlacementService,
    WaveQueue,
)


@pytest.fixture
def game_state_manager() -> GameStateManager:
    """Creates a clean GameStateManager instance for each test."""
    # We create the dependencies directly here
    economy = EconomyManager(initial_lives=20, initial_gold=100)
    placement = TowerPlacementService()
    wave_queue = WaveQueue()
    snapshot_builder = SnapshotBuilder(placement, wave_queue)

    # Create the manager with the fresh services
    gsm = GameStateManager(
        economy=economy,
        placement=placement,
        wave_queue=wave_queue,
        snapshot_builder=snapshot_builder,
    )
    return gsm


def test_build_tower_success(game_state_manager: GameStateManager):
    """Test a successful tower build operation."""
    # Arrange: The game_state_manager fixture has already created the manager.

    # Act: Player A builds a tower on a valid position (e.g., row 5, col 5).
    # We assume this tile is grass and unoccupied.
    result = game_state_manager.build_tower(
        player_id="A",
        tower_type="standard",
        tile_row=5,
        tile_col=5,
    )

    # Assert
    assert result is not None  # The result should be the tower data, not None.
    assert game_state_manager.get_player_gold("A") == 80  # 100 (start) - 20 (cost).


def test_build_tower_insufficient_gold(game_state_manager: GameStateManager):
    """Test building a tower with insufficient gold."""
    # Arrange: Manually set the player's gold to a low value.
    game_state_manager.economy.spend_gold("A", 90)  # Player A now has only 10 gold.
    assert game_state_manager.get_player_gold("A") == 10

    # Act
    result = game_state_manager.build_tower(
        player_id="A",
        tower_type="standard",  # Costs 20
        tile_row=5,
        tile_col=5,
    )

    # Assert
    assert result is None  # The operation should fail.
    assert (
        game_state_manager.get_player_gold("A") == 10
    )  # Gold balance should be unchanged.


def test_build_tower_on_invalid_terrain(game_state_manager: GameStateManager):
    """Test attempting to build on invalid terrain (e.g., water)."""
    # Arrange: Find a coordinate that is definitely not grass.
    # According to `GLOBAL_MAP_LAYOUT`, (0, 22) is water.

    # Act
    result = game_state_manager.build_tower(
        player_id="A",
        tower_type="standard",
        tile_row=0,
        tile_col=22,  # This is a water tile
    )

    # Assert
    assert result is None  # Should fail.
    # Check that the gold was refunded!
    assert game_state_manager.get_player_gold("A") == 100


def test_build_tower_in_opponent_zone(game_state_manager: GameStateManager):
    """Test Player A attempting to build in Player B's zone."""
    # Arrange: Player A tries to build in column 25 (B's zone).

    # Act
    result = game_state_manager.build_tower(
        player_id="A",
        tower_type="standard",
        tile_row=5,
        tile_col=25,  # Player B's zone
    )

    # Assert
    assert result is None
    assert game_state_manager.get_player_gold("A") == 100  # Gold should be refunded.
