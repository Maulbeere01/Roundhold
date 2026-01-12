import logging

import pygame

logger = logging.getLogger(__name__)


class DisplayManager:
    """Manages display window, render surface, and frame presentation.

    Handles all display-related operations including window initialization,
    render surface creation, and frame presentation.
    """

    def __init__(self):
        """Initialize display in fullscreen mode.

        Creates a fullscreen window and matching render surface.
        Stores screen dimensions for use in game initialization.
        """
        info = pygame.display.Info()
        native_width = info.current_w
        native_height = info.current_h

        self.screen = pygame.display.set_mode(
            (native_width, native_height), pygame.NOFRAME
        )
        logger.info(f"Windowed Fullscreen mode: {native_width}x{native_height}")

        pygame.display.set_caption("Roundhold")

        self.render_surface = pygame.Surface((native_width, native_height))

        self.screen_width = native_width
        self.screen_height = native_height

        # Clock for frame rate control
        self.clock = pygame.time.Clock()

    def present(self) -> None:
        """Present rendered frame to screen.

        Blits the render surface to the screen and flips the display buffer.
        This should be called once per frame after all rendering is complete.
        """
        self.screen.blit(self.render_surface, (0, 0))
        pygame.display.flip()

    def cleanup(self) -> None:
        pygame.quit()
