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
    "archer": [
        "Type: Archer",
        "Role: Ranged",
        "Attacks from distance.",
        "Low HP, High Damage.",
    ],
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
        
        # Animate gold display scale (pulse effect)
        target_scale = 1.0
        if game.ui_state.gold_display_scale > 1.0:
            game.ui_state.gold_display_scale = max(1.0, game.ui_state.gold_display_scale - 3.0 * (1/60))  # Decay over time
        game.ui_state.gold_display_scale += (target_scale - game.ui_state.gold_display_scale) * 0.15
        
        # Decay gold flash timer
        if game.ui_state.gold_flash_timer > 0:
            game.ui_state.gold_flash_timer = max(0, game.ui_state.gold_flash_timer - (1/60))
        
        # Calculate gold text color based on flash timer (supports gain or loss)
        flash_progress = game.ui_state.gold_flash_timer / 0.5 if game.ui_state.gold_flash_timer > 0 else 0
        base_color = game.ui_state.gold_flash_color or (255, 255, 255)
        gold_color = tuple(
            int(base_color[i] * flash_progress + 255 * (1 - flash_progress))
            for i in range(3)
        )
        
        # Render gold text with scale effect
        gold_font_size = int(28 * game.ui_state.gold_display_scale)
        gold_font = pygame.font.Font(None, gold_font_size)
        my_hud = gold_font.render(
            f"Gold: {game.player_state.my_gold}   Lives: {game.player_state.my_lives}",
            True,
            gold_color,
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
        
        # Render floating gold change texts
        self._render_floating_gold_texts(surface, game)
        
        # Render floating damage texts
        self._render_floating_damage_texts(surface, game)
        
        # Render arrow projectiles
        self._render_arrow_projectiles(surface, game)

        # 3. Send units buttons with route preview of selected unit type
        current_time = time.time()
        selected_type = game.ui_state.selected_unit_type
        selected_cost = UNIT_STATS.get(selected_type, {}).get("cost", "?")

        for i, rect in enumerate(game.ui_state.barracks_buttons, start=1):
            is_hovered = hovered_route == i
            is_recently_clicked = (
                game.ui_state.last_clicked_route == i
                and current_time - game.ui_state.click_time < 0.5
            )

            # Dynamically expand draw rect to fit preview text on hover
            draw_rect = rect.copy()
            if is_hovered:
                label = f"Route {i}"
                preview_text = f"Send: {selected_type.capitalize()} (${selected_cost})"
                label_width = font.size(label)[0]
                preview_width = font.size(preview_text)[0]
                needed_w = max(label_width, preview_width) + 20
                if needed_w > draw_rect.w:
                    draw_rect.w = needed_w
                    draw_rect.centerx = rect.centerx

            if is_recently_clicked:
                btn_color = (0, 255, 0)
            elif is_hovered:
                btn_color = (90, 120, 200)
            else:
                btn_color = (60, 60, 120)

            pygame.draw.rect(surface, btn_color, draw_rect, border_radius=6)
            if is_hovered:
                pygame.draw.rect(
                    surface, (170, 190, 255), draw_rect, width=2, border_radius=6
                )
            label = font.render(f"Route {i}", True, (255, 255, 255))
            label_rect = label.get_rect(center=(draw_rect.centerx, draw_rect.centery - 6))
            surface.blit(label, label_rect)

            # Preview the currently selected unit type & cost on hover
            if is_hovered:
                preview = font.render(
                    f"Send: {selected_type.capitalize()} (${selected_cost})",
                    True,
                    (255, 230, 180),
                )
                prev_rect = preview.get_rect(center=(draw_rect.centerx, draw_rect.centery + 10))
                surface.blit(preview, prev_rect)

        # Draw reserved/queued unit previews at route starts
        self._render_route_unit_previews(surface, game)

        # 4. Tower build button with hover feedback
        tower_hover = getattr(game.ui_state, "tower_button_hovered", False)
        tower_active = game.ui_state.tower_build_mode
        base_color = (80, 120, 80)
        hover_color = (110, 170, 110)
        active_color = (140, 210, 140)
        tower_btn_color = active_color if tower_active else (hover_color if tower_hover else base_color)

        pygame.draw.rect(
            surface, tower_btn_color, game.ui_state.tower_button, border_radius=10
        )
        if tower_hover:
            pygame.draw.rect(
                surface, (200, 255, 200), game.ui_state.tower_button, width=2, border_radius=10
            )
        tower_label = font.render("Build", True, (255, 255, 255))
        tower_label_rect = tower_label.get_rect(
            center=game.ui_state.tower_button.center
        )
        surface.blit(tower_label, tower_label_rect)
        
        # 4b. Building selection buttons (above tower button)
        self._render_building_selection_buttons(surface, game, font, mx, my)

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

    def _render_route_unit_previews(self, surface: pygame.Surface, game) -> None:
        """Render actual unit sprites at the start of each route to show queued units."""
        # Only create/update preview sprites during preparation phase
        # During combat, previews are managed by render_manager (removed as units spawn)
        if not game.phase_state.in_preparation:
            return
            
        player_id = game.player_id
        my_map = game.map_state.terrain_map
        if not my_map:
            return

        previews = getattr(game.ui_state, "route_unit_previews", {}) or {}
        
        # Track what we need vs what we have
        if not hasattr(game.ui_state, '_last_preview_state'):
            game.ui_state._last_preview_state = {}
        
        # Check if previews changed since last frame
        if game.ui_state._last_preview_state == previews:
            return  # No changes, don't recreate sprites
        
        # Instead of clearing ALL sprites, only remove/add what changed
        old_state = game.ui_state._last_preview_state
        
        # Find routes/units that were removed or changed count
        for route in list(old_state.keys()):
            if route not in previews or len(previews.get(route, [])) < len(old_state[route]):
                # Remove preview sprites for this route
                for sprite in list(game.ui_state.route_preview_sprites):
                    if hasattr(sprite, '_preview_route') and sprite._preview_route == route:
                        sprite.kill()
                        game.sim_state.render_manager.animation_manager.unregister(sprite)
                        # Also remove from units group
                        if sprite in game.sim_state.render_manager.units:
                            game.sim_state.render_manager.units.remove(sprite)
                        game.ui_state.route_preview_sprites.remove(sprite)
        
        # Store current state for next frame comparison
        game.ui_state._last_preview_state = {k: list(v) for k, v in previews.items()}
        
        if not previews:
            return

        template_manager = game.sim_state.render_manager.template_manager
        
        for route, units in previews.items():
            if player_id not in GAME_PATHS or route not in GAME_PATHS[player_id]:
                continue
            if not units:
                continue

            tile_row, tile_col = GAME_PATHS[player_id][route][0]
            base_x = my_map.rect.x + tile_col * TILE_SIZE_PX + TILE_SIZE_PX / 2
            base_y = my_map.rect.y + tile_row * TILE_SIZE_PX + TILE_SIZE_PX / 2

            # Count how many preview sprites already exist for this route
            existing_count = sum(1 for s in game.ui_state.route_preview_sprites 
                               if hasattr(s, '_preview_route') and s._preview_route == route)
            
            # Only create sprites for NEW units (beyond existing_count)
            for idx in range(existing_count, len(units)):
                u_type = units[idx]
                
                # Create offset position - spread units in a grid pattern
                col_idx = idx % 3
                row_idx = idx // 3
                dx = (col_idx - 1) * 20  # Spread horizontally
                dy = -row_idx * 24 - 30  # Stack upward from spawn
                px = base_x + dx
                py = base_y + dy

                # Create actual unit sprite for preview
                from ..sprites.units import UnitSprite
                anim_dict = template_manager.get_unit_template(u_type, player_id)
                
                preview_sprite = UnitSprite(
                    x=px,
                    y=py,
                    anim_dict=anim_dict,
                    entity_id=-1000 - idx - route * 100,  # Negative ID for previews
                )
                preview_sprite._preview_route = route
                preview_sprite._preview_index = idx
                preview_sprite._preview_player = player_id
                preview_sprite.state = "idle"
                preview_sprite.frames = anim_dict["idle"]
                
                # Add to appropriate sprite group
                game.sim_state.render_manager.units.add(preview_sprite)
                game.sim_state.render_manager.animation_manager.register(preview_sprite)
                game.ui_state.route_preview_sprites.append(preview_sprite)

    def _render_building_selection_buttons(
        self, surface: pygame.Surface, game, font: pygame.font.Font, mx: int, my: int
    ) -> None:
        """Render building selection buttons above the build button."""
        from td_shared.game import TOWER_STATS
        
        building_selection_buttons = getattr(game.ui_state, "building_selection_buttons", [])
        if not building_selection_buttons:
            return
        
        # Building display names
        building_names = {
            "standard": "Tower",
            "wood_tower": "Wood",
            "gold_mine": "Mine",
        }
        
        for rect, b_type in building_selection_buttons:
            is_selected = b_type == game.ui_state.selected_building_type
            is_hovered = rect.collidepoint(mx, my)
            
            # Colors based on building type - darker colors with good contrast
            if b_type == "gold_mine":
                base_color = (120, 100, 30)
                hover_color = (160, 130, 50)
                selected_color = (100, 80, 20)  # Darker for selected, text will be bright
                text_color = (255, 255, 200)  # Bright text for gold mine
            elif b_type == "wood_tower":
                base_color = (100, 65, 30)
                hover_color = (140, 90, 45)
                selected_color = (80, 50, 20)
                text_color = (255, 255, 255)
            else:  # standard
                base_color = (60, 60, 120)
                hover_color = (100, 100, 180)
                selected_color = (40, 120, 40)
                text_color = (255, 255, 255)
            
            if is_selected:
                color = selected_color
                border_color = (255, 255, 255)
            elif is_hovered:
                color = hover_color
                border_color = (200, 200, 255)
            else:
                color = base_color
                border_color = (100, 100, 100)
            
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=4)
            
            # Building name - use specific text color for readability
            name_text = building_names.get(b_type, b_type.capitalize())
            name_surf = font.render(name_text, True, text_color)
            name_rect = name_surf.get_rect(center=(rect.centerx, rect.centery - 6))
            surface.blit(name_surf, name_rect)
            
            # Cost - always bright gold/white for visibility
            cost = TOWER_STATS.get(b_type, {}).get("cost", "?")
            cost_surf = font.render(f"${cost}", True, (255, 255, 100))
            cost_rect = cost_surf.get_rect(center=(rect.centerx, rect.centery + 8))
            surface.blit(cost_surf, cost_rect)

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

    def _render_floating_gold_texts(self, surface: pygame.Surface, game) -> None:
        """Render floating gold indicators at mine positions only."""
        # Clear any legacy HUD floating gold texts that shouldn't exist
        if game.ui_state.floating_gold_texts:
            game.ui_state.floating_gold_texts.clear()
        
        # Render only mine gold texts (white->gold->green transition)
        self._render_floating_mine_gold_texts(surface, game)

    def _render_floating_mine_gold_texts(self, surface: pygame.Surface, game) -> None:
        """Render floating gold indicators at mine positions with white-to-green transition."""
        import time
        current_time = time.time()
        
        for text_data in list(game.ui_state.floating_mine_gold_texts):
            elapsed = current_time - text_data['start_time']
            duration = 1.5  # 1.5 second lifetime for better visibility
            
            if elapsed > duration:
                game.ui_state.floating_mine_gold_texts.remove(text_data)
                continue
            
            # Calculate animation properties
            progress = elapsed / duration
            alpha = int(255 * (1 - progress * 0.7))  # Slower fade out
            y_offset = -(progress * 50)  # Float upward
            
            # Scale effect - quick pop at start, then settle
            if progress < 0.15:
                scale = 1.0 + (0.5 * (1 - progress / 0.15))
            else:
                scale = 1.0
            
            # Color transition from bright gold to green
            # Start gold (255, 215, 0), end green (50, 255, 50)
            ease_progress = min(1.0, progress * 1.5)
            r = int(255 * (1 - ease_progress) + 50 * ease_progress)
            g = int(215 + (255 - 215) * ease_progress)
            b = int(0 * (1 - ease_progress) + 50 * ease_progress)
            color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
            
            # Render gold amount with larger, bolder font
            font_size = int(24 * scale)  # Bigger font for readability
            font = pygame.font.Font(None, font_size)
            text_surf = font.render(f"+{text_data['amount']}g", True, color)
            text_surf.set_alpha(alpha)
            
            # Add outline/shadow for better visibility
            shadow_surf = font.render(f"+{text_data['amount']}g", True, (0, 0, 0))
            shadow_surf.set_alpha(alpha // 2)
            
            # Position at mine location
            x = text_data['x'] - text_surf.get_width() // 2
            y = text_data['y'] + y_offset
            
            # Draw shadow first, then text
            surface.blit(shadow_surf, (x + 1, y + 1))
            surface.blit(text_surf, (x, y))

    def _render_floating_damage_texts(self, surface: pygame.Surface, game) -> None:
        """Render damage indicators from unit damage with proper validation."""
        import time
        
        current_time = time.time()
        duration = 1.5
        
        # Filter out expired text entries
        alive_texts = []
        for text_data in game.ui_state.floating_damage_texts:
            elapsed = current_time - text_data.get('start_time', current_time)
            if elapsed < duration:
                alive_texts.append(text_data)
            
        game.ui_state.floating_damage_texts = alive_texts
        
        # Render damage texts with color transition and fade out
        for text_data in game.ui_state.floating_damage_texts:
            try:
                elapsed = current_time - text_data.get('start_time', current_time)
                progress = min(1.0, elapsed / duration)
                
                # Color transition: white -> red, clamped to valid range
                r = 255
                g = max(0, min(255, int(255 * (1 - progress))))
                b = max(0, min(255, int(255 * (1 - progress))))
                color = (r, g, b)
                
                # Float upward
                offset_y = int(progress * 30)
                
                # Fade out in last 0.5s
                alpha = 255
                if elapsed > 1.0:
                    fade_progress = min(1.0, (elapsed - 1.0) / 0.5)
                    alpha = max(0, int(255 * (1 - fade_progress)))
                
                # Position validation - reject invalid/off-screen positions
                x = int(text_data.get('x', -1))
                y = int(text_data.get('y', -1))
                
                if x < 0 or y < 0:
                    continue
                
                y = y - offset_y
                
                # Only render if within valid screen bounds
                if not (50 <= x <= surface.get_width() - 50 and 50 <= y <= surface.get_height() - 50):
                    continue
                
                amount = int(text_data.get('amount', 0))
                if amount <= 0:
                    continue
                
                font_size = max(12, int(22 * (1 - progress * 0.3)))
                font = pygame.font.Font(None, font_size)
                damage_text = font.render(f"-{amount}", True, color)
                
                if alpha < 255:
                    damage_text.set_alpha(alpha)
                
                text_rect = damage_text.get_rect(center=(x, y))
                surface.blit(damage_text, text_rect)
            except Exception:
                # Skip any invalid text data entries
                continue

    def _render_arrow_projectiles(self, surface: pygame.Surface, game) -> None:
        """Render and update arrow projectiles flying from towers to targets."""
        import time
        import math
        current_time = time.time()
        
        for arrow in list(game.ui_state.arrow_projectiles):
            elapsed = current_time - arrow['start_time']
            progress = elapsed / arrow['duration']
            
            if progress >= 1.0:
                game.ui_state.arrow_projectiles.remove(arrow)
                continue
            
            # Interpolate position
            x = arrow['start_x'] + (arrow['end_x'] - arrow['start_x']) * progress
            y = arrow['start_y'] + (arrow['end_y'] - arrow['start_y']) * progress
            
            # Add slight arc (parabola) for visual appeal
            arc_height = 20
            arc_offset = -arc_height * 4 * progress * (1 - progress)  # Parabola peaks at 0.5
            y += arc_offset
            
            # Calculate angle from start to end
            dx = arrow['end_x'] - arrow['start_x']
            dy = arrow['end_y'] - arrow['start_y']
            angle = math.atan2(dy, dx)
            
            # Draw arrow as a line with an arrowhead
            arrow_length = 12
            arrow_width = 3
            
            # Arrow body (line)
            end_x = x
            end_y = y
            start_x = x - math.cos(angle) * arrow_length
            start_y = y - math.sin(angle) * arrow_length
            
            # Arrow color - brownish wood color
            arrow_color = (139, 90, 43)
            tip_color = (180, 180, 180)  # Silver tip
            
            # Draw arrow shaft
            pygame.draw.line(surface, arrow_color, (start_x, start_y), (end_x, end_y), arrow_width)
            
            # Draw arrowhead (triangle)
            head_length = 6
            head_width = 4
            
            # Arrowhead points
            tip = (end_x + math.cos(angle) * 2, end_y + math.sin(angle) * 2)
            left = (end_x - math.cos(angle + 0.5) * head_length, 
                    end_y - math.sin(angle + 0.5) * head_length)
            right = (end_x - math.cos(angle - 0.5) * head_length,
                     end_y - math.sin(angle - 0.5) * head_length)
            
            pygame.draw.polygon(surface, tip_color, [tip, left, right])
            
            # Draw fletching (feathers) at the back
            fletch_x = start_x - math.cos(angle) * 2
            fletch_y = start_y - math.sin(angle) * 2
            fletch_color = (200, 50, 50)  # Red feathers
            
            # Two small lines for fletching
            perp_angle = angle + math.pi / 2
            f_len = 4
            pygame.draw.line(surface, fletch_color, 
                           (fletch_x + math.cos(perp_angle) * f_len, fletch_y + math.sin(perp_angle) * f_len),
                           (fletch_x - math.cos(perp_angle) * f_len, fletch_y - math.sin(perp_angle) * f_len), 2)
