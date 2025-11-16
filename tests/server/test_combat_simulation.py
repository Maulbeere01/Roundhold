# IMPORTANT: Import tile_to_pixel to calculate a valid position
from td_shared.game import RoundResultData, SimulationData, tile_to_pixel

from server.src.td_server.core.combat_sim import run_combat_simulation


def test_tower_kills_unit():
    """
    A simple integration test scenario:
    One tower from Player A should be able to destroy a single unit from Player B
    before it reaches the base.
    """
    # Arrange: Create the initial data for the simulation.

    # FIX 1: Give the tower a strategic position.
    # Route 1 for Player B runs along the top edge of the map.
    # A position at (row 4, col 15) is close enough to this path.
    tower_pos_x, tower_pos_y = tile_to_pixel(4, 15)

    simulation_data: SimulationData = {
        "tick_rate": 20,
        "towers": [
            {
                "player_id": "A",
                "tower_type": "standard",  # 25 damage, 10 ticks cooldown
                "position_x": tower_pos_x,  # Better position
                "position_y": tower_pos_y,  # Better position
                "level": 1,
            }
        ],
        "units": [
            {
                "player_id": "B",
                "unit_type": "standard",  # 50 HP
                "route": 1,  # A valid route for Player B
                "spawn_tick": 0,
            }
        ],
    }

    # Act: Run the entire simulation.
    result: RoundResultData = run_combat_simulation(simulation_data)

    # Assert: Check the results.

    # FIX 2: We check if Player A (whose base is under attack)
    # lost ZERO lives, because the unit should have been intercepted.
    assert (
        result["lives_lost_player_A"] == 0
    ), "Player A should not lose a life because the unit should be killed."

    # Player B was not attacked, so they should not lose any lives either.
    assert result["lives_lost_player_B"] == 0

    # Player A should get gold for the kill.
    assert result["gold_earned_player_A"] > 0

    # Player B should get no gold.
    assert result["gold_earned_player_B"] == 0
