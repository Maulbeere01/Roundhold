from __future__ import annotations

import time

import pygame
from td_shared.game import GAME_PATHS, TILE_SIZE_PX, UNIT_STATS

# Unit descriptions for tooltips
UNIT_DESCRIPTIONS = {
    "standard": [
        "Type: Warrior",
        "Role: Swarm / DPS",
        "Fast and cheap.",
        "Good for early game.",
    ],
    "pawn": ["Type: Pawn", "Role: Tank", "Slow but high HP.", "Distracts towers."],
}


class HUDRenderer:
    """Renders HUD, buttons, timers, and overlays."""

    def render(self, game) -> None:
        surface = game.display_manager.render_surface
        mx, my = pygame.mouse.get_pos()

        # 1. Route path highlight
        hovered_route = game.ui_state.hovered_route
        if hovered_route is not None:
            self._render_route_highlight(surface, game, hovered_route)

        # 2. Basic HUD (Gold and Lives)
        font = pygame.font.Font(None, 28)
        my_hud = font.render(
            f"Gold: {game.player_state.my_gold}   Lives: {game.player_state.my_lives}",
            True,
            (255, 255, 255),
        )
        opp_hud = font.render(
            f"Opponent Lives: {game.player_state.opponent_lives}", True, (255, 200, 200)
        )

        if game.player_id == "B":
            right_x = game.display_manager.screen_width - 20 - my_hud.get_width()
            surface.blit(my_hud, (right_x, 20))
            surface.blit(opp_hud, (20, 20))
        else:
            surface.blit(my_hud, (20, 20))
            right_x = game.display_manager.screen_width - 20 - opp_hud.get_width()
            surface.blit(opp_hud, (right_x, 20))

        # 3. Send units buttons
        current_time = time.time()
        for i, rect in enumerate(game.ui_state.barracks_buttons, start=1):
            is_hovered = hovered_route == i
            is_recently_clicked = (
                game.ui_state.last_clicked_route == i
                and current_time - game.ui_state.click_time < 0.5
            )

            if is_recently_clicked:
                btn_color = (0, 255, 0)
            elif is_hovered:
                btn_color = (100, 100, 180)
            else:
                btn_color = (60, 60, 120)

            pygame.draw.rect(surface, btn_color, rect, border_radius=6)
            if is_hovered:
                pygame.draw.rect(
                    surface, (150, 150, 255), rect, width=2, border_radius=6
                )
            label = font.render(f"Send route {i}", True, (255, 255, 255))
            label_rect = label.get_rect(center=rect.center)
            surface.blit(label, label_rect)

        # 4. Tower build button
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

        # 5. Timers
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

        # 6. Hover overlay for build mode
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

        # 7. Debug overlays
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

        # 8. Unit selection buttons and tooltip handling
        tooltip_unit_type = None  # Store hovered unit type

        if game.ui_state.unit_selection_buttons:
            for rect, u_type in game.ui_state.unit_selection_buttons:
                is_selected = u_type == game.ui_state.selected_unit_type
                is_hovered = rect.collidepoint(mx, my)

                if is_hovered:
                    tooltip_unit_type = u_type

                if is_selected:
                    color = (0, 255, 0)
                    border_color = (255, 255, 255)
                elif is_hovered:
                    color = (100, 100, 180)
                    border_color = (200, 200, 255)
                else:
                    color = (60, 60, 120)
                    border_color = (100, 100, 100)

                pygame.draw.rect(surface, color, rect, border_radius=6)
                pygame.draw.rect(surface, border_color, rect, width=2, border_radius=6)

                name_text = font.render(u_type.capitalize(), True, (255, 255, 255))
                name_rect = name_text.get_rect(center=(rect.centerx, rect.centery - 8))
                surface.blit(name_text, name_rect)

                cost = UNIT_STATS.get(u_type, {}).get("cost", "?")
                cost_text = font.render(f"${cost}", True, (255, 215, 0))
                cost_rect = cost_text.get_rect(center=(rect.centerx, rect.centery + 10))
                surface.blit(cost_text, cost_rect)

        # 9. Draw tooltip on top of everything
        if tooltip_unit_type:
            self._draw_unit_tooltip(surface, mx, my, tooltip_unit_type)

    def _render_route_highlight(
        self, surface: pygame.Surface, game, route: int
    ) -> None:
        """Render a highlight overlay on the tiles of the hovered route."""
        player_id = game.player_id
        if player_id not in GAME_PATHS or route not in GAME_PATHS[player_id]:
            return

        path_tiles = GAME_PATHS[player_id][route]
        my_map = game.map_state.terrain_map

        highlight_color = (255, 220, 100, 100)

        for tile_row, tile_col in path_tiles:
            tile_x = my_map.rect.x + tile_col * TILE_SIZE_PX
            tile_y = my_map.rect.y + tile_row * TILE_SIZE_PX

            highlight_surface = pygame.Surface(
                (TILE_SIZE_PX, TILE_SIZE_PX), pygame.SRCALPHA
            )
            highlight_surface.fill(highlight_color)
            surface.blit(highlight_surface, (tile_x, tile_y))

    def _draw_unit_tooltip(
        self, surface: pygame.Surface, mx: int, my: int, unit_type: str
    ) -> None:
        """Draw a tooltip box with unit stats and description."""
        stats = UNIT_STATS.get(unit_type, {})
        description_lines = UNIT_DESCRIPTIONS.get(unit_type, ["Unknown Unit"])

        # Fonts
        title_font = pygame.font.Font(None, 26)
        text_font = pygame.font.Font(None, 22)

        # Colors
        bg_color = (20, 20, 30, 230)  # Semi-transparent dark background
        border_color = (200, 200, 200)
        text_color = (220, 220, 220)
        stat_color = (100, 255, 100)  # Green for stats

        # Prepare lines
        lines = []

        # Stats line (HP, Speed, Damage)
        hp = stats.get("health", "?")
        speed = stats.get("speed", "?")
        damage = stats.get("base_damage", 1)
        lines.append((f"HP: {hp}  Dmg: {damage}  Spd: {int(speed)}", stat_color))

        # Add description lines
        for line in description_lines:
            lines.append((line, text_color))

        # Calculate box size
        max_width = 0
        line_height = 20
        padding = 10

        rendered_lines = []
        for text, color in lines:
            surf = (
                title_font.render(text, True, color)
                if color == stat_color
                else text_font.render(text, True, color)
            )
            if surf.get_width() > max_width:
                max_width = surf.get_width()
            rendered_lines.append(surf)

        box_width = max_width + (padding * 2)
        box_height = (len(rendered_lines) * line_height) + (padding * 2)

        # Position box above mouse
        box_x = mx + 15
        box_y = my - box_height - 10

        # Prevent clipping off screen
        screen_w, screen_h = surface.get_size()
        if box_x + box_width > screen_w:
            box_x = mx - box_width - 10
        if box_y < 0:
            box_y = my + 20

        # Draw background box
        rect = pygame.Rect(box_x, box_y, box_width, box_height)
        box_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, bg_color, box_surf.get_rect(), border_radius=5)
        pygame.draw.rect(
            box_surf, border_color, box_surf.get_rect(), width=1, border_radius=5
        )
        surface.blit(box_surf, (box_x, box_y))

        # Draw text lines
        y_offset = box_y + padding
        for surf in rendered_lines:
            surface.blit(surf, (box_x + padding, y_offset))
            y_offset += line_height
