"""Main entry point for the game client."""
import logging

import pygame

from .assets.loader import AssetLoader
from .assets.template_manager import TemplateManager
from .config import AssetPaths, GameSettings
from .map import (TILE_SIZE,TileMap, get_terrain_maps)
from td_shared.map import PlacementGrid, mirror_paths_for_width
from td_shared.game import GAME_PATHS, TOWER_STATS, MAP_WIDTH_TILES
from .sprites.buildings import BuildingSprite
from .display import DisplayManager
from .rendering import RenderManager
from .debug import DebugRenderer
from .wave_simulator import WaveSimulator
from .network import NetworkClient
from td_shared.game import RoundStartData, SimulationData, PlayerID, PREP_SECONDS, COMBAT_SECONDS, START_GOLD, PLAYER_LIVES
from td_shared.protobuf import proto_to_sim_data
from .ui.input_controller import InputController
from .ui.build_controller import BuildController
from .ui.hud_renderer import HUDRenderer

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameSimulation:
    """Encapsulates the running game (rendering + simulation)."""
    
    def __init__(self, display_manager: DisplayManager, asset_loader: AssetLoader, asset_paths: AssetPaths, settings: GameSettings, player_id: PlayerID, network_client: NetworkClient):
        # Store dependencies
        self.settings = settings
        self.asset_paths = asset_paths
        self.asset_loader = asset_loader
        self.display_manager = display_manager
        self.player_id: PlayerID = player_id
        self.network_client = network_client
        
        self._initialize_game_state()
        self._initialize_maps()
        self._initialize_grids()
        self._initialize_renderer()
        self._initialize_simulation()
        self._initialize_controllers()
        self._initialize_ui_state()
        self._initialize_ui_elements()
        
        logger.info("GameSimulation initialized")
    
    def _initialize_renderer(self) -> None:
        self.template_manager = TemplateManager(self.asset_loader)
        self.render_manager = RenderManager(
            self.display_manager.render_surface,
            self.template_manager,
            self.settings,
            TILE_SIZE,
            self.display_manager.screen_width,
            self.display_manager.screen_height,
            self.player_id
        )
        self.render_manager.set_maps(self.left_map, self.right_map)
        self.render_manager.initialize_water_background()
        self.render_manager.initialize_environment_effects(
            self.left_map,
            self.right_map,
            self.settings.vertical_offset,
            self.left_map_width,
            self.center_x
        )
        self.render_manager.initialize_sprites(
            self.center_x,
            self.center_y,
            self.left_map_width,
            self.settings.vertical_offset
        )
    
    def _initialize_simulation(self) -> None:
        self.wave_simulator = WaveSimulator()
        self.settings.show_grid = False
        self.settings.show_grid_coords = False
        self.debug_renderer = DebugRenderer(self.settings)
    
    def _initialize_controllers(self) -> None:
        self.build_controller = BuildController(self)
        self.input_controller = InputController(self.build_controller, self.debug_renderer)
        self.hud_renderer = HUDRenderer()
    
    def _initialize_ui_state(self) -> None:
        self.my_gold = START_GOLD
        self.my_lives = PLAYER_LIVES
        self.opponent_lives = PLAYER_LIVES
        
        self.current_round = 0  # Track current round for RoundAck
        self._round_result_received = False
        self._round_ack_sent = False
        
        self._round_base_my_lives = self.my_lives
        self._round_base_opponent_lives = self.opponent_lives
        
        self.in_preparation: bool = False
        self.in_combat: bool = False
        self.prep_seconds_total: float = PREP_SECONDS
        self.combat_seconds_total: float = COMBAT_SECONDS
        self.prep_seconds_remaining: float = 0.0
        self.combat_seconds_remaining: float = 0.0
    
    def _initialize_ui_elements(self) -> None:
        # send units buttons 
        if self.player_id == "A":
            sidebar_x = 20  
        else:
            sidebar_x = self.display_manager.screen_width - 180 
        top_y = 100
        w, h, pad = 160, 36, 12
        self.barracks_buttons = [
            pygame.Rect(sidebar_x, top_y + i * (h + pad), w, h) for i in range(5)
        ]
        logger.info("Barracks buttons at: %s", [tuple((r.x, r.y, r.w, r.h)) for r in self.barracks_buttons])
        
        # Tower build UI 
        tower_button_w, tower_button_h = 80, 80
        if self.player_id == "A":
            tower_button_x = self.center_x - self.left_map_width - TILE_SIZE + 20
        else:
            tower_button_x = self.center_x + TILE_SIZE + self.right_map_width - tower_button_w - 20
        tower_button_y = self.display_manager.screen_height - tower_button_h - 20
        self.tower_button = pygame.Rect(tower_button_x, tower_button_y, tower_button_w, tower_button_h)
        
        # Build mode state
        self.tower_build_mode = False  # Whether tower placement mode is active
        self.hover_tile: tuple[int, int] | None = None  # (row, col) of hovered tile
        self._local_towers: dict[tuple[str, int, int], "BuildingSprite"] = {}  # (player_id,row,col) -> sprite
    
    def _get_my_map_and_grid(self):
        return self.get_player_map(self.player_id), self.get_player_grid(self.player_id)
    
    def get_player_grid(self, player_id: PlayerID) -> PlacementGrid:
        return self.placement_grid_A if player_id == "A" else self.placement_grid_B
    
    def get_player_map(self, player_id: PlayerID) -> "TileMap":
        return self.left_map if player_id == "A" else self.right_map
    
    def _initialize_game_state(self) -> None:
        self.center_x = self.display_manager.screen_width // 2
        self.center_y = self.display_manager.screen_height // 2
    
    def _initialize_maps(self) -> None:
        self.flat_tileset = self.asset_loader.load_image(self.asset_paths.tileset_flat)
        elevation_tileset = self.asset_loader.load_image(self.asset_paths.tileset_elevation)
        
        left_map_data, right_map_data = get_terrain_maps()
        
        self.left_map_width = len(left_map_data[0]) * TILE_SIZE
        self.right_map_width = len(right_map_data[0]) * TILE_SIZE
        
        self.left_map = TileMap(
            left_map_data,
            tileset_surface=self.flat_tileset,
            offset_x=self.center_x - self.left_map_width - TILE_SIZE,
            offset_y=self.settings.vertical_offset,
            elevation_tileset=elevation_tileset
        )
        self.right_map = TileMap(
            right_map_data,
            tileset_surface=self.flat_tileset,
            offset_x=self.center_x + TILE_SIZE,
            offset_y=self.settings.vertical_offset,
            elevation_tileset=elevation_tileset
        )

    def _initialize_grids(self) -> None:
        """Create and populate placement grids for both sides."""
        # Derive grid size from left/right map data
        # (rows = len(tile_map), cols = len(tile_map[0]))
        left_rows = len(get_terrain_maps()[0])
        left_cols = len(get_terrain_maps()[0][0])
        right_rows = len(get_terrain_maps()[1])
        right_cols = len(get_terrain_maps()[1][0])

        self.placement_grid_A = PlacementGrid(left_cols, left_rows)
        self.placement_grid_B = PlacementGrid(right_cols, right_rows)
        # Populate A with GAME_PATHS
        self.placement_grid_A.populate_from_paths(GAME_PATHS)
        # Populate B by mirroring columns across width-1
        mirrored_paths = mirror_paths_for_width(GAME_PATHS, MAP_WIDTH_TILES)
        self.placement_grid_B.populate_from_paths(mirrored_paths)

    def load_round_start(self, round_start: RoundStartData) -> None:
        # New combat round from server 
        self.current_round += 1
        logger.info("Loading RoundStart for round %d", self.current_round)
        self._clear_local_towers()
        self._round_result_received = False
        self._round_ack_sent = False
        # Capture current lives as baseline for this round's local visualization
        self._round_base_my_lives = self.my_lives
        self._round_base_opponent_lives = self.opponent_lives
        # Switch to combat timer
        self.in_preparation = False
        self.in_combat = True
        self.combat_seconds_remaining = self.combat_seconds_total
        self.wave_simulator.load_wave(round_start["simulation_data"])

    def load_initial_round_preview(self, round_start: RoundStartData) -> None:
        # Initial snapshot sent with MatchFound; do NOT increment round or set flags
        logger.info("Loading initial preview snapshot (no round increment)")
        self.wave_simulator.load_wave(round_start["simulation_data"])
    
    def handle_event(self, event) -> None:
        self.input_controller.handle_event(event, self)

    def update(self, dt: float):
        """Update game state and animations.
        
        Args:
            dt: Delta time in seconds since last frame
        """
        self.wave_simulator.update(dt)
        self.render_manager.update(dt)
        
        # Sync sprites to simulation state
        state = self.wave_simulator.game_state
        if state:
            self.render_manager.sync_sprites_to_state(state)
            # Update local lives counter during simulation using round baselines (visual only)
            if not self._round_result_received:
                if self.player_id == "A":
                    my_vis = self._round_base_my_lives - int(getattr(state, "lives_lost_player_A", 0))
                    opp_vis = self._round_base_opponent_lives - int(getattr(state, "lives_lost_player_B", 0))
                else:
                    my_vis = self._round_base_my_lives - int(getattr(state, "lives_lost_player_B", 0))
                    opp_vis = self._round_base_opponent_lives - int(getattr(state, "lives_lost_player_A", 0))
                self.my_lives = max(0, my_vis)
                self.opponent_lives = max(0, opp_vis)
        # Update phase timers
        if self.in_preparation:
            self.prep_seconds_remaining = max(0.0, self.prep_seconds_remaining - dt)
            if self.prep_seconds_remaining <= 0.0:
                self.in_preparation = False
        if self.in_combat:
            self.combat_seconds_remaining = max(0.0, self.combat_seconds_remaining - dt)
            # End of combat on timer is visual only, authoritative end comes via RoundResult
            # Ack as soon as local simulation finished for this round (RoundResult follows after ACKs)
            if (
                not self._round_ack_sent
                and self.current_round > 0
                and state.is_simulation_complete()
            ):
                logger.info("Simulation complete for round %d, sending RoundAck", self.current_round)
                self.network_client.round_ack(player_id=self.player_id, round_number=self.current_round)
                self._round_ack_sent = True
    
    def render(self) -> None:
        """Render game world, sprites, and UI."""
        self.render_manager.draw(self.left_map, self.right_map)
        self.hud_renderer.render(self)
        
        self.display_manager.present()
    
    def _remove_local_tower(self, player_id: str, row: int, col: int) -> None:
        self.build_controller.remove_tower(player_id, row, col)

    def _clear_local_towers(self) -> None:
        for sprite in self._local_towers.values():
            sprite.kill()
        self._local_towers.clear()

    def _on_build_response(self, success: bool, *, row: int, col: int) -> None:
        """Handle server response to tower build request."""
        if success:
            logger.info("BuildTower succeeded (server confirmed) at (%d,%d)", row, col)
        else:
            logger.warning("BuildTower rejected by server at (%d,%d), rolling back", row, col)
            # Server rejected: refund gold and remove tower from grid
            tower_cost = int(TOWER_STATS["standard"]["cost"])
            self.my_gold += tower_cost
            my_grid = self.get_player_grid(self.player_id)
            # Rollback: remove sprite and free tile
            self._remove_local_tower(self.player_id, row, col)
            my_grid.clear_tower(row, col)
            logger.info("Rolled back tower at (%d,%d)", row, col)
    
    def _on_send_units_response(self, success: bool, total_gold: int | None) -> None:
        """Update local gold immediately based on server ACK for SendUnits."""
        if success and total_gold is not None:
            logger.info("SendUnits acknowledged by server, updating gold to %d", total_gold)
            self.my_gold = int(total_gold)
        elif not success and total_gold is not None:
            # Keep UI in sync even on rejection (e.g., due to insufficient gold)
            self.my_gold = int(total_gold)
    
class GameApp:
    """Top-level app with menu -> waiting -> game state machine."""
    def __init__(self):
        pygame.init()
        self.settings = GameSettings()
        self.asset_paths = AssetPaths()
        self.asset_loader = AssetLoader(self.asset_paths)
        self.display_manager = DisplayManager()
        self.network_client = NetworkClient()
        self.clock = self.display_manager.clock
        self.game_state: str = "MENU"
        self.game: GameSimulation | None = None
        self.player_id: PlayerID | None = None
        self.menu_button_rect = pygame.Rect(
            self.display_manager.screen_width // 2 - 120,
            self.display_manager.screen_height // 2 - 30,
            240,
            60
        )
        self.waiting_message: str = "Connecting..."
    
    
    def run(self) -> None:
        running = True
        try:
            while running:
                dt = self.clock.tick(self.settings.fps) / 1000.0
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self._handle_state_event(event)
                self._update_state(dt)
                self._render_state()
        finally:
            self.display_manager.cleanup()
    
    def _handle_state_event(self, event) -> None:
        if self.game_state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.menu_button_rect.collidepoint(event.pos):
                    logger.info("User clicked Find Match, queuing...")
                    self.network_client.queue_for_match(
                        player_name="Player",
                        on_match_found=self._on_match_found,
                        on_queue_update=self._on_queue_update,
                        on_round_start=self._on_round_start,
                        on_round_result=self._on_round_result,
                        on_tower_placed=self._on_tower_placed,
                    )
                    self.game_state = "WAITING"
        elif self.game_state == "GAME" and self.game is not None:
            self.game.handle_event(event)
    
    def _update_state(self, dt: float) -> None:
        if self.game_state == "GAME" and self.game is not None:
            self.game.update(dt)
    
    def _render_state(self) -> None:
        surface = self.display_manager.render_surface
        surface.fill((10, 20, 28))
        if self.game_state == "MENU":
            pygame.draw.rect(surface, (60, 120, 200), self.menu_button_rect, border_radius=8)
            font = pygame.font.Font(None, 36)
            text = font.render("Find Match", True, (255, 255, 255))
            text_rect = text.get_rect(center=self.menu_button_rect.center)
            surface.blit(text, text_rect)
        elif self.game_state == "WAITING":
            font = pygame.font.Font(None, 32)
            text = font.render(self.waiting_message, True, (220, 220, 220))
            surface.blit(text, (self.display_manager.screen_width // 2 - text.get_width() // 2,
                                self.display_manager.screen_height // 2 - text.get_height() // 2))
        elif self.game_state == "GAME" and self.game is not None:
            self.game.render()
        self.display_manager.present()
    
    def _on_queue_update(self, message: str) -> None:
        logger.debug("Queue update: %s", message)
        self.waiting_message = message
    
    def _on_match_found(self, player_id: str, round_start_pb) -> None:
        logger.info("Match found. Assigned player_id=%s", player_id)
        # Convert proto RoundStartData to dict shape expected by GameSimulation
        simulation_data: SimulationData = proto_to_sim_data(round_start_pb.simulation_data)
        round_start: RoundStartData = {"simulation_data": simulation_data}
        # Initialize game simulation
        self.player_id = player_id  # type: ignore[assignment]
        self.game = GameSimulation(self.display_manager, self.asset_loader, self.asset_paths, self.settings, player_id, self.network_client)  # type: ignore[arg-type]
        # Start preparation timer; load initial snapshot without incrementing the round counter
        self.game.in_preparation = True
        self.game.in_combat = False
        self.game.prep_seconds_remaining = self.game.prep_seconds_total
        self.game.load_initial_round_preview(round_start)
        self.game_state = "GAME"

    def _on_round_start(self, round_start_pb) -> None:
        logger.info("RoundStart event received")
        if self.game is None:
            return
        simulation_data: SimulationData = proto_to_sim_data(round_start_pb.simulation_data)
        round_start: RoundStartData = {"simulation_data": simulation_data}
        self.game.load_round_start(round_start)
    
    def _on_round_result(self, round_result_pb) -> None:
        """Apply authoritative server results (overrides local simulation)."""
        if self.game is None or self.player_id is None:
            return
        logger.info("RoundResult: A -%d +%d, B -%d +%d (authoritative totals: A %d lives/%d gold, B %d lives/%d gold)",
                    round_result_pb.lives_lost_player_A,
                    round_result_pb.gold_earned_player_A,
                    round_result_pb.lives_lost_player_B,
                    round_result_pb.gold_earned_player_B,
                    round_result_pb.total_lives_player_A,
                    round_result_pb.total_gold_player_A,
                    round_result_pb.total_lives_player_B,
                    round_result_pb.total_gold_player_B)
        # Override local values with authoritative server totals
        if self.player_id == "A":
            self.game.my_lives = int(round_result_pb.total_lives_player_A)
            self.game.my_gold = int(round_result_pb.total_gold_player_A)
            self.game.opponent_lives = int(round_result_pb.total_lives_player_B)
        else:
            self.game.my_lives = int(round_result_pb.total_lives_player_B)
            self.game.my_gold = int(round_result_pb.total_gold_player_B)
            self.game.opponent_lives = int(round_result_pb.total_lives_player_A)
        # Mark that result arrived; ack will be sent when local simulation finishes
        self.game._round_result_received = True
        # Transition back to preparation countdown for next round
        self.game.in_combat = False
        self.game.in_preparation = True
        self.game.prep_seconds_remaining = self.game.prep_seconds_total

    def _on_tower_placed(self, tower_placed_pb) -> None:
        """Render opponent (or my) tower immediately on server broadcast."""
        if self.game is None:
            return
        player_id = tower_placed_pb.player_id
        row = int(tower_placed_pb.tile_row)
        col = int(tower_placed_pb.tile_col)
        # Update placement grid
        grid = self.game.get_player_grid(player_id)
        if grid.is_buildable(row, col):
            grid.place_tower(row, col)
        # Spawn immediate tower sprite with range indicator
        self.game.build_controller.spawn_tower(player_id, row, col, "standard")


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
