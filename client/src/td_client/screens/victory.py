from __future__ import annotations

import pygame

from .base import Screen


class VictoryScreen(Screen):
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.app.switch_screen("MENU")

    def update(self, dt: float) -> None:
        return None

    def render(self, surface: pygame.Surface) -> None:
        font = pygame.font.Font(None, 72)
        text = font.render("You Won! Opponent left.", True, (100, 255, 100))
        w = self.app.display_manager.screen_width
        h = self.app.display_manager.screen_height
        surface.blit(
            text,
            (w // 2 - text.get_width() // 2, h // 2 - text.get_height() // 2),
        )
