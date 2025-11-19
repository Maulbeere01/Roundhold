from __future__ import annotations

from dataclasses import dataclass

import pygame
from td_client.debug import DebugRenderer
from td_client.map import TileMap
from td_client.rendering import RenderManager
from td_client.sprites import BuildingSprite
from td_client.ui import BuildController, HUDRenderer, InputController
from td_client.wave_simulator import WaveSimulator
from td_shared import PlacementGrid


@dataclass
class MapState:
    """Map-related state: terrain, grids, dimensions."""

    center_x: int = 0
    center_y: int = 0
    flat_tileset: pygame.Surface | None = None
    map_width: int = 0
    map_rows: int = 0
    map_cols: int = 0
    terrain_map: TileMap | None = None
    placement_grid_A: PlacementGrid | None = None
    placement_grid_B: PlacementGrid | None = None


@dataclass
class PlayerState:
    """Player game state: gold, lives, rounds."""

    my_gold: int = 0
    my_lives: int = 0
    opponent_lives: int = 0
    current_round: int = 0
    round_ack_sent: bool = False
    round_result_received: bool = False
    round_base_my_lives: int = 0
    round_base_opponent_lives: int = 0


@dataclass
class PhaseState:
    """Game phase state: preparation/combat timers."""

    in_preparation: bool = False
    in_combat: bool = False
    prep_seconds_total: float = 0.0
    prep_seconds_remaining: float = 0.0
    combat_seconds_total: float = 0.0
    combat_seconds_remaining: float = 0.0


@dataclass
class UIState:
    """UI elements and interaction state."""

    barracks_buttons: list[pygame.Rect] = None
    tower_button: pygame.Rect | None = None
    tower_build_mode: bool = False
    hover_tile: tuple[int, int] | None = None
    local_towers: dict[tuple[str, int, int], BuildingSprite] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.barracks_buttons is None:
            self.barracks_buttons = []
        if self.local_towers is None:
            self.local_towers = {}


@dataclass
class SimulationState:
    """Simulation components: renderer, controllers, wave simulator."""

    wave_simulator: WaveSimulator | None = None
    debug_renderer: DebugRenderer | None = None
    render_manager: RenderManager | None = None
    build_controller: BuildController | None = None
    input_controller: InputController | None = None
    hud_renderer: HUDRenderer | None = None
