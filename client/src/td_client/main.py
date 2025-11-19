import logging

import pygame

from td_client.assets import AssetLoader
from td_client.config import AssetPaths, GameSettings
from td_client.display import DisplayManager
from td_client.network import NetworkClient, NetworkEventRouter
from td_client.screens import (
    GameScreen,
    MenuScreen,
    Screen,
    VictoryScreen,
    WaitingScreen,
)

logger = logging.getLogger(__name__)


class GameApp:
    """Top level app that manages the active screen and game loop."""

    def __init__(self):
        pygame.init()

        self.settings = GameSettings()
        self.asset_paths = AssetPaths()
        self.asset_loader = AssetLoader(self.asset_paths)
        self.display_manager = DisplayManager()
        self.clock = self.display_manager.clock

        # Network, Event Router for  all Events send by server through the QueueForMatch stream
        self.network_client = NetworkClient()
        self.router = NetworkEventRouter(self)

        self.screens: dict[str, Screen] = {
            "MENU": MenuScreen(self),
            "WAITING": WaitingScreen(self),
            "GAME": GameScreen(self),
            "VICTORY": VictoryScreen(self),
        }

        self.current_screen: Screen = self.screens["MENU"]

    def switch_screen(self, name: str, **kwargs) -> None:
        logger.info("Switching to screen: %s", name)
        self.current_screen = self.screens[name]
        self.current_screen.enter(**kwargs)

    # Game Loop
    def run(self) -> None:
        running = True
        try:
            while running:
                # time since last frame in seconds
                dt = self.clock.tick(self.settings.fps) / 1000.0

                for event in pygame.event.get():
                    if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                    ):
                        running = False
                    else:
                        self.current_screen.handle_event(event)

                self.current_screen.update(dt)

                surface = self.display_manager.render_surface
                surface.fill((10, 20, 28))
                self.current_screen.render(surface)
                self.display_manager.present()

        finally:
            self.display_manager.cleanup()
            self.network_client.close()


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
