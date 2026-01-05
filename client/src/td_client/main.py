import logging

import pygame

from td_client.assets import AssetLoader
from td_client.config import AssetPaths, GameSettings
from td_client.display import DisplayManager
from td_client.events import EventBus
from td_client.network import NetworkClient, NetworkEventRouter, NetworkHandler
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

        # Central event bus for all client-side communication
        self.event_bus = EventBus()
        self.event_bus.set_main_thread()

        # Network client, handler (subscribes to action events), and router (publishes network events)
        self.network_client = NetworkClient()
        self.network_handler = NetworkHandler(self.network_client, self.event_bus)
        self.router = NetworkEventRouter(self, self.event_bus)

        self.screens: dict[str, Screen] = {
            "MENU": MenuScreen(self),
            "WAITING": WaitingScreen(self),
            "GAME": GameScreen(self),
            "VICTORY": VictoryScreen(self),
        }

        self.current_screen: Screen = self.screens["MENU"]

    def switch_screen(self, name: str, **kwargs) -> None:
        logger.info("Switching to screen: %s", name)
        # Clean up subscriptions from the old screen
        self.current_screen.exit()
        self.current_screen = self.screens[name]
        self.current_screen.enter(**kwargs)

    # Game Loop
    def run(self) -> None:
        running = True
        try:
            while running:
                # time since last frame in seconds
                dt = self.clock.tick(self.settings.fps) / 1000.0

                # Process any pending events from background threads (network)
                self.event_bus.process_pending()

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
            self.event_bus.clear()
            self.network_handler.cleanup()
            self.display_manager.cleanup()
            self.network_client.close()


def main():
    app = GameApp()
    app.run()


if __name__ == "__main__":
    main()
