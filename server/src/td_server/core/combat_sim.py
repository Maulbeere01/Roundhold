from __future__ import annotations

from td_shared.game import GOLD_PER_KILL, RoundResultData, SimulationData
from td_shared.simulation import GameState


def run_combat_simulation(simulation_data: SimulationData) -> RoundResultData:
    """Run server-authoritative combat and return aggregated results."""
    game_state = GameState(simulation_data)
    while not game_state.is_simulation_complete():
        game_state.update_tick()

    # Use tracked lives lost from simulation (units reaching base)
    lives_lost_player_A = game_state.lives_lost_player_A
    lives_lost_player_B = game_state.lives_lost_player_B

    gold_A = game_state.get_kills_by_player("A") * GOLD_PER_KILL
    gold_B = game_state.get_kills_by_player("B") * GOLD_PER_KILL

    result: RoundResultData = {
        "lives_lost_player_A": lives_lost_player_A,
        "gold_earned_player_A": gold_A,
        "lives_lost_player_B": lives_lost_player_B,
        "gold_earned_player_B": gold_B,
    }
    return result
