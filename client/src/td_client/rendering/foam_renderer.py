"""Foam renderer for animated water-land boundaries."""

import pygame

from ..sprites.animation import AnimatedObject


class FoamRenderer(AnimatedObject):
    """Renders animated foam at specified positions"""

    FOAM_FRAMES = 8  # Number of horizontal frames in spritesheet
    FOAM_FPS = 7

    FOAM_OFFSET_Y = -0.68  # Vertical position adjustment factor (relative to tile_size)
    FOAM_SCALE_FACTOR = 3.1  # Size multiplier relative to tile_size
    FOAM_EDGE_INSET = 3  # Horizontal inset for outer 2 tiles on each side (pixels)

    def __init__(
        self,
        foam_frames: list[pygame.Surface],
        foam_positions: list[tuple[int, int, bool]],
        tile_size: int,
        screen_width: int,
        screen_height: int,
    ):
        """
        Args:
            foam_frames: List of pre-extracted animation frame surfaces (not yet scaled)
            foam_positions: List of (x, y, is_left_island) pixel positions where foam should appear
            tile_size: Size of tiles in pixels (for scaling)
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.tile_size = tile_size
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.frames = self._scale_frames(foam_frames)

        self.frame_duration = 1.0 / self.FOAM_FPS
        self.current_frame_index = 0
        self.animation_time = 0.0

        self.foam_positions = foam_positions

        self.foam_surface = pygame.Surface(
            (screen_width, screen_height), pygame.SRCALPHA
        )

    def _scale_frames(self, frames: list[pygame.Surface]) -> list[pygame.Surface]:
        """Scale foam frames to correct size based on tile_size and scale factor

        Args:
            frames: List of unscaled frame surfaces

        Returns:
            List of scaled frame surfaces
        """
        if not frames:
            return frames

        original_frame_width = frames[0].get_width()
        original_frame_height = frames[0].get_height()

        base_scale_factor = self.tile_size / original_frame_width
        scaled_width = int(self.tile_size * self.FOAM_SCALE_FACTOR)
        scaled_height = int(
            original_frame_height * base_scale_factor * self.FOAM_SCALE_FACTOR
        )

        scaled_frames = []
        for frame in frames:
            scaled_frame = pygame.transform.scale(frame, (scaled_width, scaled_height))
            scaled_frames.append(scaled_frame.convert_alpha())

        return scaled_frames

    def update_animation(self, dt: float) -> None:
        """Update animation state.

        Args:
            dt: Delta time in seconds since last frame
        """
        if not self.frames or len(self.frames) <= 1:
            return

        self.animation_time += dt

        if self.animation_time >= self.frame_duration:
            self.animation_time = 0.0
            self.current_frame_index += 1

            if self.current_frame_index >= len(self.frames):
                self.current_frame_index = 0

    def _calculate_horizontal_inset(self, idx: int, total_count: int) -> int:
        """move the 2 outermost tiles 3 pixels inwards

        Args:
            idx: Position index in sorted list
            total_count: Total number of positions

        Returns:
            Horizontal inset in pixels
        """
        if idx < 2:
            return self.FOAM_EDGE_INSET
        elif idx >= total_count - 2:
            return -self.FOAM_EDGE_INSET
        return 0

    def _render_foam_at_position(
        self,
        x: int,
        y: int,
        horizontal_inset: int,
        current_frame: pygame.Surface,
        foam_offset_y_pixels: int,
        foam_width: int,
        foam_height: int,
    ) -> None:
        """Render foam frame at specific position

        Args:
            x: X position
            y: Y position
            horizontal_inset: Horizontal adjustment in pixels
            current_frame: Current animation frame
            foam_offset_y_pixels: Vertical offset in pixels
            foam_width: Width of foam frame
            foam_height: Height of foam frame
        """
        if foam_width > self.tile_size:
            draw_x = x + (self.tile_size - foam_width) // 2 + horizontal_inset
        else:
            draw_x = x + horizontal_inset

        draw_y = y + foam_offset_y_pixels

        self.foam_surface.blit(current_frame, (draw_x, draw_y))

    def get_surface(self) -> pygame.Surface:
        """Return surface with current foam animation frame

        Returns:
            Surface with rendered foam animation
        """
        if not self.frames:
            return self.foam_surface

        self.foam_surface.fill((0, 0, 0, 0))

        current_frame = self.frames[self.current_frame_index]
        foam_offset_y_pixels = int(self.tile_size * self.FOAM_OFFSET_Y)
        foam_width, foam_height = current_frame.get_size()

        left_positions = sorted(
            [(x, y) for x, y, is_left in self.foam_positions if is_left],
            key=lambda p: p[0],
        )
        right_positions = sorted(
            [(x, y) for x, y, is_left in self.foam_positions if not is_left],
            key=lambda p: p[0],
        )

        for idx, (x, y) in enumerate(left_positions):
            horizontal_inset = self._calculate_horizontal_inset(
                idx, len(left_positions)
            )
            self._render_foam_at_position(
                x,
                y,
                horizontal_inset,
                current_frame,
                foam_offset_y_pixels,
                foam_width,
                foam_height,
            )

        for idx, (x, y) in enumerate(right_positions):
            horizontal_inset = self._calculate_horizontal_inset(
                idx, len(right_positions)
            )
            self._render_foam_at_position(
                x,
                y,
                horizontal_inset,
                current_frame,
                foam_offset_y_pixels,
                foam_width,
                foam_height,
            )

        return self.foam_surface
