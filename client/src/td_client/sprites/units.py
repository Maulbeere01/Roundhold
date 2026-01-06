"""Unit sprites - movable entities."""
from typing import Dict, List, Callable, Optional
import random
import pygame
from .animated import AnimatedSprite

class UnitSprite(AnimatedSprite):
    """Movable unit sprite with Idle / Run / Attack states."""

    Y_OFFSET = 35
    HEALTH_LERP_SPEED = 120.0  # hp per second for smoothing
    HIT_FLASH_TIME = 0.25      # seconds of flash after taking damage

    def __init__(
        self,
        x: float,
        y: float,
        anim_dict: Dict[str, List[pygame.Surface]],
        speed: float = 40.0,
        entity_id: int = -1,
        on_death: Optional[Callable[[float, float], None]] = None,
        **kwargs
    ):
        self.animations = anim_dict
        self.state = "idle"

        # Default animation FPS
        kwargs.setdefault("fps", 10.0)
        super().__init__(x, y, self.animations["idle"], entity_id=entity_id, **kwargs)

        self.speed = speed
        self.facing_right = True

        self.last_x = x
        self.last_y = y
        self.last_dx = 0
        self.last_dy = 0
        self.time_since_last_move = 0.0

        # Attack finishing state
        self.is_finishing_attack = False
        self.attack_loops_left = 0

        # Callback to trigger explosion
        self.on_death = on_death 

        # Health tracking (set via update_health)
        self.max_health: float = 1.0
        self.health: float = 1.0
        self.health_display: float = 1.0
        self.hit_flash_timer: float = 0.0
        self.health_bar_width = 32
        self.health_bar_height = 5

    def set_position(self, x: float, y: float) -> None:
        """Update position unless the unit is finishing an attack."""
        if self.is_finishing_attack:
            return

        dx = x - self.last_x
        dy = y - self.last_y

        if abs(dx) > 0.001 or abs(dy) > 0.001:
            self.last_dx = dx
            self.last_dy = dy

        if abs(dx) > 0.01:
            if x < self.last_x:
                self.facing_right = False
            elif x > self.last_x:
                self.facing_right = True

        if abs(dx) + abs(dy) > 0.001:
            self.time_since_last_move = 0.0

        self.last_x = x
        self.last_y = y

        super().set_position(x, y + self.Y_OFFSET)

    def update_health(self, health: float, max_health: float, game_ui_state=None) -> None:
        """Update health values and trigger a brief flash on damage."""
        max_health = max(1.0, float(max_health))
        health = max(0.0, min(float(health), max_health))

        if health < self.health_display - 0.001:
            self.hit_flash_timer = self.HIT_FLASH_TIME
            
            # Spawn floating damage text
            damage = self.health_display - health
            if game_ui_state and hasattr(game_ui_state, 'floating_damage_texts'):
                import time
                game_ui_state.floating_damage_texts.append({
                    'amount': int(damage),
                    'x': self.rect.centerx,
                    'y': self.rect.top - 10,
                    'start_time': time.time()
                })

        self.max_health = max_health
        self.health = health

    def trigger_base_attack(self):
        """Called when the unit reaches the enemy base (server removes it)."""
        if self.is_finishing_attack:
            return

        self.is_finishing_attack = True

        # Select attack animation based on direction
        abs_dx = abs(self.last_dx)
        abs_dy = abs(self.last_dy)

        if abs_dx > abs_dy:
            self.state = "atk_side"
        else:
            if self.last_dy > 0:
                self.state = "atk_down"
            else:
                self.state = "atk_up"

        self.frames = self.animations.get(self.state, self.animations["idle"])
        self.current_frame_index = 0
        self.attack_loops_left = 2

    def update_animation(self, dt: float) -> None:
        """Advance animation frames and handle attack looping."""
        
        # --- Special logic for finishing attack ---
        if self.is_finishing_attack:
            self.animation_time += dt
            if self.animation_time >= self.frame_duration:
                self.animation_time = 0.0
                self.current_frame_index += 1

                if self.current_frame_index >= len(self.frames):
                    self.current_frame_index = 0
                    self.attack_loops_left -= 1

                    # Death logic
                    if self.attack_loops_left <= 0:
                        # Trigger explosion callback once
                        if self.on_death:
                            # Pass current center to callback
                            self.on_death(self.rect.centerx, self.rect.centery)
                            self.on_death = None # Prevent double triggering
                            
                        self.kill() # Remove unit sprite
                        return

            # Render logic for attack
            current_frame = self.frames[self.current_frame_index]
            if not self.facing_right and self.state == "atk_side":
                self.image = pygame.transform.flip(current_frame, True, False)
            else:
                self.image = current_frame
            return

        # --- Normal logic ---
        super().update_animation(dt)
        current_frame = self.frames[self.current_frame_index]

        if not self.facing_right:
            self.image = pygame.transform.flip(current_frame, True, False)
        else:
            self.image = current_frame

    def update(self, dt: float):
        """Handle state switching."""
        if self.is_finishing_attack:
            self.update_animation(dt)
            return

        self.time_since_last_move += dt

        if self.time_since_last_move < 0.15:
            target_state = "run"
        else:
            target_state = "idle"

        if self.state != target_state:
            self.state = target_state
            self.frames = self.animations[target_state]
            self.current_frame_index = 0

        self.update_animation(dt)

        # Smoothly animate health bar toward actual health
        if self.health_display > self.health:
            self.health_display = max(
                self.health, self.health_display - self.HEALTH_LERP_SPEED * dt
            )
        elif self.health_display < self.health:
            self.health_display = min(
                self.health, self.health_display + self.HEALTH_LERP_SPEED * dt
            )

        if self.hit_flash_timer > 0:
            self.hit_flash_timer = max(0.0, self.hit_flash_timer - dt)

    def draw_on(self, surface: pygame.Surface):
        """Draw the unit and a compact health bar above it."""
        jitter = 0
        if self.hit_flash_timer > 0:
            jitter = max(1, int(2 * (self.hit_flash_timer / self.HIT_FLASH_TIME)))
        offset_x = random.randint(-jitter, jitter) if jitter else 0
        offset_y = random.randint(-jitter, jitter) if jitter else 0

        dest_rect = self.rect.move(offset_x, offset_y)
        surface.blit(self.image, dest_rect)

        if self.hit_flash_timer > 0:
            flash = self.image.copy()
            flash.fill((200, 30, 30), special_flags=pygame.BLEND_RGB_ADD)
            surface.blit(flash, dest_rect)

        if self.max_health <= 0:
            return

        ratio = max(0.0, min(1.0, self.health_display / self.max_health))
        bar_w = self.health_bar_width
        bar_h = self.health_bar_height
        bar_x = int(dest_rect.centerx - bar_w / 2)
        bar_y = int(dest_rect.top - bar_h - 6)

        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        fg_rect = pygame.Rect(bar_x + 1, bar_y + 1, int((bar_w - 2) * ratio), bar_h - 2)

        pygame.draw.rect(surface, (25, 25, 25), bg_rect)
        flash_boost = self.hit_flash_timer / self.HIT_FLASH_TIME if self.HIT_FLASH_TIME > 0 else 0.0
        flash_boost = max(0.0, min(1.0, flash_boost))
        base_color = (60, 200, 90)
        flash_color = (255, 230, 140)
        color = tuple(
            int(base_color[i] * (1 - flash_boost) + flash_color[i] * flash_boost)
            for i in range(3)
        )
        pygame.draw.rect(surface, color, fg_rect)