from typing import Dict, List
import pygame

from .base import YSortableSprite
from .animated import AnimatedSprite

class BuildingSprite(YSortableSprite):
    """Static building sprite (castles, towers, etc.).

    Buildings are static structures that do not move or animate.
    Position is set via rect.midbottom for correct ground reference.
    """

    def __init__(
        self,
        x: float,
        y: float,
        image: pygame.Surface,
        entity_id: int = -1,
        range_px: float = 0.0,
        range_fill_color: tuple[int, int, int, int] = (0, 180, 255, 50),
        range_outline_color: tuple[int, int, int, int] = (0, 140, 220, 140),
    ):
        """Initialize building sprite."""
        super().__init__(x, y, image, entity_id)
        self._range_surface: pygame.Surface | None = None
        self._range_rect: pygame.Rect | None = None

        if range_px > 0:
            self._create_range_indicator(
                range_px, range_fill_color, range_outline_color
            )

    def _create_range_indicator(
        self,
        range_px: float,
        fill_color: tuple[int, int, int, int],
        outline_color: tuple[int, int, int, int],
    ) -> None:
        radius = int(range_px)
        diameter = radius * 2
        surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (radius, radius)

        pygame.draw.circle(surface, fill_color, center, radius)
        pygame.draw.circle(surface, outline_color, center, radius, width=2)

        self._range_surface = surface
        self._range_rect = surface.get_rect(
            center=(self.rect.midbottom[0], self.rect.midbottom[1])
        )

    def set_position(self, x: float, y: float) -> None:
        super().set_position(x, y)
        if self._range_rect is not None:
            self._range_rect.center = (x, y)

    def get_range_overlay(self) -> tuple[pygame.Surface, pygame.Rect] | None:
        if self._range_surface and self._range_rect:
            return self._range_surface, self._range_rect
        return None


class MannedTowerSprite(BuildingSprite):
    """A tower with an animated unit standing on top."""

    def __init__(
        self,
        x: float,
        y: float,
        image: pygame.Surface,
        archer_anims: Dict[str, List[pygame.Surface]],
        player_id: str = "A", 
        entity_id: int = -1,
        range_px: float = 0.0,
        archer_offset_y: int = -45,
    ):
        super().__init__(x, y, image, entity_id, range_px)
        
        self.archer_anims = archer_anims
        self.archer_offset_y = archer_offset_y
        self.archer_alive = True 

        # Position archer on top of tower.
        # self.rect.bottom is the ground y-coordinate.
        archer_x = x
        archer_y = self.rect.bottom - 40 # offset archer to match tower sprite
        
        # Initialize with Idle
        self.archer = AnimatedSprite(
            archer_x, archer_y, 
            frames=archer_anims["idle"], 
            fps=10.0
        )
        
        self.state = "idle"
        
        # LOGIC FOR MIRRORING:
        # Player A (Left side) -> Faces Right (True)
        # Player B (Right side) -> Faces Left (False)
        self.facing_right = (player_id == "A") 

    def update_facing(self, target_x: float, target_y: float):
        """Determine direction based on target position."""
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        
        # Flip logic based on target
        if dx < 0:
            self.facing_right = False
        else:
            self.facing_right = True

        # Direction logic (Animation state)
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        new_state = "idle"
        
        if abs_dx > abs_dy:
            new_state = "atk_side"
        else:
            if dy > 0:
                new_state = "atk_down"
            else:
                new_state = "atk_up"
        
        if self.state != new_state:
            self.state = new_state
            self.archer.frames = self.archer_anims[new_state]
            self.archer.current_frame_index = 0

    def reset_to_idle(self):
        """Reset to idle animation, but keep default facing direction."""
        if self.state != "idle":
            self.state = "idle"
            self.archer.frames = self.archer_anims["idle"]
            self.archer.current_frame_index = 0

    def update_animation(self, dt: float):
        """Update archer animation frame and apply flipping."""
        # If archer no longer exists (castle destroyed), skip updates
        if not self.archer_alive:
            return

        # Update child animation
        self.archer.update_animation(dt)

        # Handle flipping
        # If facing_right is False (Player B default, or aiming left), we flip the sprite.
        current_frame = self.archer.frames[self.archer.current_frame_index]

        if not self.facing_right:
            self.archer.image = pygame.transform.flip(current_frame, True, False)
        else:
            self.archer.image = current_frame

    def kill_archer(self) -> tuple[float, float] | None:
        """Kills the archer and returns their center position for effects."""
        if not self.archer_alive:
            return None
            
        self.archer_alive = False
        return self.archer.rect.center

    def draw_on(self, surface: pygame.Surface):
        """Draw tower then archer."""
        surface.blit(self.image, self.rect)
        # Draw archer only if alive
        if self.archer_alive:
            # Ensure archer stays anchored to its calculated position
            self.archer.rect = self.archer.image.get_rect(midbottom=self.archer.rect.midbottom)
            surface.blit(self.archer.image, self.archer.rect)