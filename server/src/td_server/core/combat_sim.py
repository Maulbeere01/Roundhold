from __future__ import annotations

from td_shared.game import RoundResultData, SimulationData
from td_shared.simulation import GameState


def run_combat_simulation(simulation_data: SimulationData) -> RoundResultData:
    """Run server-authoritative combat and return aggregated results."""
    game_state = GameState(simulation_data)
    while not game_state.is_simulation_complete():
        game_state.update_tick()

    # Use tracked lives lost from simulation (units reaching base)
    lives_lost_player_A = game_state.lives_lost_player_A
    lives_lost_player_B = game_state.lives_lost_player_B

    # Get gold earned from kills (already calculated per unit type)
    gold_A = game_state.get_gold_earned_by_player("A")
    gold_B = game_state.get_gold_earned_by_player("B")

    result: RoundResultData = {
        "lives_lost_player_A": lives_lost_player_A,
        "gold_earned_player_A": gold_A,
        "lives_lost_player_B": lives_lost_player_B,
        "gold_earned_player_B": gold_B,
    }
    return result
