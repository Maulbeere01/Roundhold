from td_shared.game import SimulationData
from td_shared.simulation import GameState

# Prevent the accumulator from growing without bound if the render loop stalls.
MAX_ACCUMULATED_TIME = 0.5


class WaveSimulator:
    """Synchronises the deterministic simulation with the render loop"""

    def __init__(self) -> None:
        self._game_state: GameState | None = None
        self._accumulator: float = 0.0

    @property
    def game_state(self) -> GameState | None:
        """Return the currently loaded game state, if any"""
        return self._game_state

    def load_wave(self, simulation_data: SimulationData) -> GameState:
        """Create a new game state from simulation data and reset the accumulator"""
        game_state = GameState(simulation_data)
        self._game_state = game_state
        self._accumulator = 0.0
        return game_state

    def update(self, dt: float) -> int:
        """Advance the simulation by consuming accumulated time in fixed steps"""
        if self._game_state is None or dt <= 0.0:
            return 0

        game_state = self._game_state
        if game_state.is_simulation_complete():
            return 0

        self._accumulator += dt
        if self._accumulator > MAX_ACCUMULATED_TIME:
            self._accumulator = MAX_ACCUMULATED_TIME

        ticks_processed = 0
        sim_dt = game_state.sim_dt

        while self._accumulator >= sim_dt and not game_state.is_simulation_complete():
            game_state.update_tick()
            self._accumulator -= sim_dt
            ticks_processed += 1

        return ticks_processed
