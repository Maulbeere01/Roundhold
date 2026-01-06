from __future__ import annotations

from dataclasses import dataclass

import pygame
from td_shared import PlacementGrid

from ..debug import DebugRenderer
from ..map import TileMap
from ..rendering import RenderManager
from ..sprites import BuildingSprite
from ..ui import BuildController, HUDRenderer, InputController
from .wave_simulator import WaveSimulator


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
    placement_grid: PlacementGrid | None = None


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
    unit_selection_buttons: list[tuple[pygame.Rect, str]] = None # List of (Rect, unit_type)
    selected_unit_type: str = "standard" # Default to Warrior
    tower_build_mode: bool = False
    hover_tile: tuple[int, int] | None = None
    hovered_route: int | None = None  # Route number (1-5) being hovered, or None
    last_clicked_route: int | None = None  # Last clicked route for visual feedback
    click_time: float = 0.0  # Time when route was last clicked
    local_towers: dict[tuple[str, int, int], BuildingSprite] = None
    tower_button_hovered: bool = False
    route_unit_previews: dict[int, list[str]] | None = None
    route_preview_sprites: list = None
    route_preview_sprites: list = None
    floating_gold_texts: list = None  # List of floating gold change indicators
    gold_display_scale: float = 1.0  # Scale pulse for gold display
    floating_damage_texts: list = None  # List of floating damage indicators

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.barracks_buttons is None:
            self.barracks_buttons = []
        if self.local_towers is None:
            self.local_towers = {}
        if self.unit_selection_buttons is None:
            self.unit_selection_buttons = []
        if self.route_unit_previews is None:
            self.route_unit_previews = {}
        if self.route_preview_sprites is None:
            self.route_preview_sprites = []
        if self.route_preview_sprites is None:
            self.route_preview_sprites = []
        if self.floating_gold_texts is None:
            self.floating_gold_texts = []
        if self.floating_damage_texts is None:
            self.floating_damage_texts = []


@dataclass
class SimulationState:
    """Simulation components: renderer, controllers, wave simulator."""

    wave_simulator: WaveSimulator | None = None
    debug_renderer: DebugRenderer | None = None
    render_manager: RenderManager | None = None
    build_controller: BuildController | None = None
    input_controller: InputController | None = None
    hud_renderer: HUDRenderer | None = None
