from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
from td_shared import (
    COMBAT_SECONDS,
    GLOBAL_MAP_LAYOUT,
    PLAYER_LIVES,
    PREP_SECONDS,
    START_GOLD,
    TILE_SIZE_PX,
    PlayerID,
)

from client.src.td_client.audio.audio import AudioService

if TYPE_CHECKING:
    from ..assets import AssetLoader
    from ..config import AssetPaths, GameSettings
    from ..display import DisplayManager
    from ..events import EventBus
    from ..network import NetworkClient
    from .game_simulation import GameSimulation

from ..assets import TemplateManager
from ..debug import DebugRenderer
from ..map import TileMap, get_visual_map_from_layout
from ..rendering import RenderManager
from ..ui import BuildController, HUDRenderer, InputController
from .wave_simulator import WaveSimulator

logger = logging.getLogger(__name__)


class GameFactory:
    """Factory for creating and initializing a GameSimulation instance.

    heavy initialization happens in factory methods.
    Enables reload, restart, and hot-reload capabilities.
    """

    @staticmethod
    def create_game(
        display_manager: DisplayManager,
        asset_loader: AssetLoader,
        asset_paths: AssetPaths,
        settings: GameSettings,
        player_id: PlayerID,
        network_client: NetworkClient,
        audio: AudioService,
        event_bus: EventBus | None = None,
    ) -> GameSimulation:
        """Create and fully initialize a GameSimulation instance.

        Args:
            display_manager: Display manager instance
            asset_loader: Asset loader instance
            asset_paths: Asset paths configuration
            settings: Game settings
            player_id: Player identifier ("A" or "B")
            network_client: Network client instance
            event_bus: Central event bus for client communication

        Returns:
            Fully initialized GameSimulation instance
        """
        from .game_simulation import GameSimulation

        # Create instance
        game = GameSimulation(
            display_manager=display_manager,
            asset_loader=asset_loader,
            asset_paths=asset_paths,
            settings=settings,
            player_id=player_id,
            network_client=network_client,
            audio=audio,
            event_bus=event_bus,
        )

        # Initialize all components
        GameFactory._initialize_map_and_grids(game)
        GameFactory._initialize_rendering(game)
        GameFactory._initialize_simulation(game)
        GameFactory._initialize_controllers(game)
        GameFactory._initialize_ui(game)

        logger.info("GameSimulation fully initialized via GameFactory")
        return game

    @staticmethod
    def _initialize_map_and_grids(game: GameSimulation) -> None:
        """Initialize map, terrain, and placement grids."""
        from td_shared import PlacementGrid

        # Calculate screen center
        game.map_state.center_x = game.display_manager.screen_width // 2
        game.map_state.center_y = game.display_manager.screen_height // 2

        # Load and setup map
        game.map_state.flat_tileset = game.asset_loader.load_image(
            game.asset_paths.tileset_flat
        )
        map_data = get_visual_map_from_layout()

        game.map_state.map_width = len(map_data[0]) * TILE_SIZE_PX
        game.map_state.map_rows = len(map_data)
        game.map_state.map_cols = len(map_data[0])

        offset_x = (game.display_manager.screen_width - game.map_state.map_width) // 2

        game.map_state.terrain_map = TileMap(
            map_data,
            tileset_surface=game.map_state.flat_tileset,
            offset_x=offset_x,
            offset_y=game.settings.vertical_offset,
            asset_loader=game.asset_loader,
        )

        # Initialize placement grid
        game.map_state.placement_grid = PlacementGrid(GLOBAL_MAP_LAYOUT)

    @staticmethod
    def _initialize_rendering(game: GameSimulation) -> None:
        """Initialize rendering components."""
        game.sim_state.render_manager = RenderManager(
            game.display_manager.render_surface,
            TemplateManager(game.asset_loader),
            game.settings,
            TILE_SIZE_PX,
            game.display_manager.screen_width,
            game.display_manager.screen_height,
            game.player_id,
        )
        game.sim_state.render_manager.initialize(game)

    @staticmethod
    def _initialize_simulation(game: GameSimulation) -> None:
        game.sim_state.wave_simulator = WaveSimulator()
        game.sim_state.debug_renderer = DebugRenderer(game.settings)

    @staticmethod
    def _initialize_controllers(game: GameSimulation) -> None:
        game.sim_state.build_controller = BuildController(game)
        game.sim_state.input_controller = InputController(
            game.sim_state.build_controller, game.sim_state.debug_renderer
        )

    @staticmethod
    def _initialize_ui(game: GameSimulation) -> None:
        # Preconditions
        assert START_GOLD >= 0, f"START_GOLD must be >= 0, not {START_GOLD}"
        assert PLAYER_LIVES >= 0, f"PLAYER_LIVES must be >= 0, not {PLAYER_LIVES}"
        assert PREP_SECONDS > 0, f"PREP_SECONDS must be > 0, not {PREP_SECONDS}"
        assert COMBAT_SECONDS > 0, f"COMBAT_SECONDS must be > 0, not {COMBAT_SECONDS}"

        # Player state
        game.player_state.my_gold = START_GOLD
        game.player_state.my_lives = PLAYER_LIVES
        game.player_state.opponent_lives = PLAYER_LIVES
        game.player_state.current_round = 0
        game.player_state.round_result_received = False
        game.player_state.round_ack_sent = False
        game.player_state.round_base_my_lives = game.player_state.my_lives
        game.player_state.round_base_opponent_lives = game.player_state.opponent_lives

        # Phase state
        game.phase_state.in_preparation = False
        game.phase_state.in_combat = False
        game.phase_state.prep_seconds_total = PREP_SECONDS
        game.phase_state.combat_seconds_total = COMBAT_SECONDS
        game.phase_state.prep_seconds_remaining = 0.0
        game.phase_state.combat_seconds_remaining = 0.0

        # Postconditions
        assert (
            game.player_state.my_gold == START_GOLD
        ), "my_gold not initialized correctly"
        assert (
            game.player_state.my_lives == PLAYER_LIVES
        ), "my_lives not initialized correctly"
        assert (
            game.player_state.opponent_lives == PLAYER_LIVES
        ), "opponent_lives not initialized correctly"
        assert (
            game.player_state.current_round == 0
        ), "current_round not initialized to 0"
        assert game.player_state.my_gold >= 0, "my_gold must be >= 0"
        assert game.player_state.my_lives >= 0, "my_lives must be >= 0"
        assert game.player_state.opponent_lives >= 0, "opponent_lives must be >= 0"
        assert (
            not game.phase_state.in_preparation
        ), "Should not be in preparation initially"
        assert not game.phase_state.in_combat, "Should not be in combat initially"
        assert game.phase_state.prep_seconds_total > 0, "prep_seconds_total must be > 0"
        assert (
            game.phase_state.combat_seconds_total > 0
        ), "combat_seconds_total must be > 0"

        # UI elements
        game.sim_state.hud_renderer = HUDRenderer()
        GameFactory._initialize_ui_buttons(game)

    @staticmethod
    def _initialize_ui_buttons(game: GameSimulation) -> None:
        # Barracks buttons
        sidebar_x = (
            20 if game.player_id == "A" else game.display_manager.screen_width - 180
        )
        top_y = 100
        w, h, pad = 160, 36, 12
        game.ui_state.barracks_buttons = [
            pygame.Rect(sidebar_x, top_y + i * (h + pad), w, h) for i in range(5)
        ]
        logger.info(
            "Barracks buttons at: %s",
            [tuple((r.x, r.y, r.w, r.h)) for r in game.ui_state.barracks_buttons],
        )

        # Tower build button
        tower_button_w, tower_button_h = 80, 80
        if game.player_id == "A":
            tower_button_x = 20
        else:
            tower_button_x = game.display_manager.screen_width - tower_button_w - 20
        tower_button_y = game.display_manager.screen_height - tower_button_h - 20
        game.ui_state.tower_button = pygame.Rect(
            tower_button_x, tower_button_y, tower_button_w, tower_button_h
        )

        # Build mode state
        game.ui_state.tower_build_mode = False
        game.ui_state.hover_tile = None
        game.ui_state.local_towers = {}
        game.ui_state.local_gold_mines = {}

        unit_types = ["standard", "pawn", "archer"]
        btn_width = 100
        btn_height = 50
        gap = 20

        total_width = (len(unit_types) * btn_width) + ((len(unit_types) - 1) * gap)
        start_x = (game.display_manager.screen_width - total_width) // 2
        y_pos = game.display_manager.screen_height - 70  # Near bottom

        game.ui_state.unit_selection_buttons = []
        for i, u_type in enumerate(unit_types):
            x = start_x + i * (btn_width + gap)
            rect = pygame.Rect(x, y_pos, btn_width, btn_height)
            game.ui_state.unit_selection_buttons.append((rect, u_type))

        game.ui_state.selected_unit_type = "standard"

        # Building type selection buttons (above tower button)
        building_types = ["standard", "wood_tower", "gold_mine"]
        bldg_btn_width = 90
        bldg_btn_height = 35
        bldg_gap = 5

        # Position building buttons above the tower button
        bldg_y_start = (
            tower_button_y
            - bldg_btn_height * len(building_types)
            - bldg_gap * (len(building_types) - 1)
            - 10
        )

        game.ui_state.building_selection_buttons = []
        for i, b_type in enumerate(building_types):
            bldg_x = tower_button_x + (tower_button_w - bldg_btn_width) // 2
            bldg_y = bldg_y_start + i * (bldg_btn_height + bldg_gap)
            rect = pygame.Rect(bldg_x, bldg_y, bldg_btn_width, bldg_btn_height)
            game.ui_state.building_selection_buttons.append((rect, b_type))

        game.ui_state.selected_building_type = "standard"
