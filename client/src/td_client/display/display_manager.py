import logging

import pygame

logger = logging.getLogger(__name__)


class DisplayManager:
    """Manages display window, render surface, and frame presentation.

    Handles all display-related operations including window initialization,
    render surface creation, and frame presentation.
    """

    def __init__(self):
        """Initialize display in windowed mode.

        Creates a resizable windowed mode at native screen size.
        Stores screen dimensions for use in game initialization.
        """
        info = pygame.display.Info()
        self.native_width = info.current_w
        self.native_height = info.current_h
        self.is_fullscreen = False

        # Start in windowed mode (resizable) at full screen size
        self.screen = pygame.display.set_mode(
            (self.native_width, self.native_height), pygame.RESIZABLE
        )
        logger.info(f"Windowed mode: {self.native_width}x{self.native_height}")

        pygame.display.set_caption("Roundhold")

        self.render_surface = pygame.Surface((self.native_width, self.native_height))

        self.screen_width = self.native_width
        self.screen_height = self.native_height

        # Clock for frame rate control
        self.clock = pygame.time.Clock()

    def toggle_fullscreen(self) -> None:
        """Toggle between fullscreen and windowed mode.
        
        Preserves the current render surface and switches display mode.
        """
        self.is_fullscreen = not self.is_fullscreen
        
        if self.is_fullscreen:
            # Switch to fullscreen
            self.screen = pygame.display.set_mode(
                (self.native_width, self.native_height), pygame.FULLSCREEN
            )
            logger.info(f"Switched to fullscreen: {self.native_width}x{self.native_height}")
        else:
            # Switch to windowed mode (resizable)
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height), pygame.RESIZABLE
            )
            logger.info(f"Switched to windowed mode: {self.screen_width}x{self.screen_height}")

    def handle_resize(self, width: int, height: int) -> None:
        """Handle window resize event.
        
        Updates screen dimensions and recreates render surface.
        Only applies in windowed mode.
        """
        if not self.is_fullscreen:
            self.screen_width = width
            self.screen_height = height
            self.render_surface = pygame.Surface((width, height))
            logger.info(f"Window resized to: {width}x{height}")

    def present(self) -> None:
        """Present rendered frame to screen.

        Blits the render surface to the screen and flips the display buffer.
        This should be called once per frame after all rendering is complete.
        """
        self.screen.blit(self.render_surface, (0, 0))
        pygame.display.flip()

    def cleanup(self) -> None:
        pygame.quit()
