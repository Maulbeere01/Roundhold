from __future__ import annotations

import pygame
from td_shared.game import GAME_PATHS, TILE_SIZE_PX


class HUDRenderer:
    """Renders HUD, buttons, timers, overlays."""

    def render(self, game) -> None:
        surface = game.display_manager.render_surface
        hovered_route = game.ui_state.hovered_route
        
        # Render route path highlight if hovering over a route button
        if hovered_route is not None:
            self._render_route_highlight(surface, game, hovered_route)
        
        # Basic HUD
        font = pygame.font.Font(None, 28)
        my_hud = font.render(
            f"Gold: {game.player_state.my_gold}   Lives: {game.player_state.my_lives}",
            True,
            (255, 255, 255),
        )
        opp_hud = font.render(
            f"Opponent Lives: {game.player_state.opponent_lives}",
            True,
            (255, 200, 200),
        )
        if game.player_id == "B":
            right_x = game.display_manager.screen_width - 20 - my_hud.get_width()
            surface.blit(my_hud, (right_x, 20))
            surface.blit(opp_hud, (20, 20))
        else:
            surface.blit(my_hud, (20, 20))
            right_x = game.display_manager.screen_width - 20 - opp_hud.get_width()
            surface.blit(opp_hud, (right_x, 20))        # Send units buttons (highlight if hovered or clicked)
        import time
        current_time = time.time()
        for i, rect in enumerate(game.ui_state.barracks_buttons, start=1):
            is_hovered = (hovered_route == i)
            is_recently_clicked = (game.ui_state.last_clicked_route == i and 
                                  current_time - game.ui_state.click_time < 0.5)
            
            # TEST: Use bright green for recently clicked buttons
            if is_recently_clicked:
                btn_color = (0, 255, 0)  # Bright green when clicked
            elif is_hovered:
                btn_color = (100, 100, 180)  # Brighter blue when hovered
            else:
                btn_color = (60, 60, 120)  # Dark blue default
                
            pygame.draw.rect(surface, btn_color, rect, border_radius=6)
            if is_hovered:
                # Draw a border to emphasize the hovered button
                pygame.draw.rect(surface, (150, 150, 255), rect, width=2, border_radius=6)
            label = font.render(f"Send route {i}", True, (255, 255, 255))
            label_rect = label.get_rect(center=rect.center)
            surface.blit(label, label_rect)

        # Tower build button
        tower_btn_color = (
            (120, 200, 120) if game.ui_state.tower_build_mode else (80, 120, 80)
        )
        pygame.draw.rect(
            surface, tower_btn_color, game.ui_state.tower_button, border_radius=8
        )
        tower_label = font.render("Tower", True, (255, 255, 255))
        tower_label_rect = tower_label.get_rect(
            center=game.ui_state.tower_button.center
        )
        surface.blit(tower_label, tower_label_rect)

        # Timers
        timer_font = pygame.font.Font(None, 32)
        center_x = game.display_manager.screen_width // 2
        if game.phase_state.in_preparation:
            prep_text = timer_font.render(
                f"Prep: {int(game.phase_state.prep_seconds_remaining)}s",
                True,
                (200, 220, 255),
            )
            surface.blit(prep_text, (center_x - prep_text.get_width() // 2, 20))
        if game.phase_state.in_combat:
            combat_text = timer_font.render(
                f"Combat: {int(game.phase_state.combat_seconds_remaining)}s",
                True,
                (255, 220, 200),
            )
            y = 20 if not game.phase_state.in_preparation else 20 + 24
            surface.blit(combat_text, (center_x - combat_text.get_width() // 2, y))

        # Hover overlay
        if game.ui_state.tower_build_mode and game.ui_state.hover_tile:
            my_map = game.map_state.terrain_map
            row, col = game.ui_state.hover_tile
            tile_x = my_map.rect.x + col * TILE_SIZE_PX
            tile_y = my_map.rect.y + row * TILE_SIZE_PX
            hover_surface = pygame.Surface(
                (TILE_SIZE_PX, TILE_SIZE_PX), pygame.SRCALPHA
            )
            hover_surface.fill((0, 0, 0, 80))
            surface.blit(hover_surface, (tile_x, tile_y))

        # Debug overlays
        game.sim_state.debug_renderer.draw_grid(
            game.display_manager.render_surface,
            game.map_state.center_x,
            game.map_state.map_width,
            game.settings.vertical_offset,
            placement_grid=game.map_state.placement_grid,
            origin=(
                game.map_state.terrain_map.rect.x,
                game.map_state.terrain_map.rect.y,
            ),
        )
        game.sim_state.debug_renderer.draw_info_text(
            game.display_manager.render_surface
        )

    def _render_route_highlight(self, surface: pygame.Surface, game, route: int) -> None:
        """Render a highlight overlay on the tiles of the hovered route."""
        player_id = game.player_id
        
        # Get path positions for this player's route
        if player_id not in GAME_PATHS or route not in GAME_PATHS[player_id]:
            return
        
        path_tiles = GAME_PATHS[player_id][route]
        terrain_map = game.map_state.terrain_map
        
        # Create a semi-transparent highlight color (yellow-ish glow)
        highlight_color = (255, 220, 100, 100)  # RGBA with alpha
        
        for tile_row, tile_col in path_tiles:
            tile_x = terrain_map.rect.x + tile_col * TILE_SIZE_PX
            tile_y = terrain_map.rect.y + tile_row * TILE_SIZE_PX
            
            # Create a highlight surface for this tile
            highlight_surface = pygame.Surface(
                (TILE_SIZE_PX, TILE_SIZE_PX), pygame.SRCALPHA
            )
            highlight_surface.fill(highlight_color)
            surface.blit(highlight_surface, (tile_x, tile_y))