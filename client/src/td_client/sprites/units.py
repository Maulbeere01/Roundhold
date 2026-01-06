"""Unit sprites - movable entities."""
from typing import Dict, List, Callable, Optional
import pygame
from .animated import AnimatedSprite

class UnitSprite(AnimatedSprite):
    """Movable unit sprite with Idle / Run / Attack states."""

    Y_OFFSET = 35

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