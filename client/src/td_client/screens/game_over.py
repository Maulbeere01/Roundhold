import pygame

from .base import Screen
import sys

class GameOverScreen(Screen):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.result_text = "GAME OVER"
        self.color = (255, 255, 255)

        w = app.display_manager.screen_width
        h = app.display_manager.screen_height

        # Exit
        self.btn_rect = pygame.Rect(w // 2 - 100, h // 2 + 50, 200, 50)

    def enter(self, **kwargs) -> None:
        super().enter(**kwargs)

        won = kwargs.get("won", False)
        reason = kwargs.get("reason", "")

        if won:
            self.result_text = "VICTORY!"
            self.color = (50, 255, 50)  # Grün
        else:
            self.result_text = "DEFEAT"
            self.color = (255, 50, 50)  # Rot

        if reason:
            self.result_text += f" ({reason})"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_rect.collidepoint(event.pos):
                pygame.quit()
                sys.exit()

    def render(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()

        # Title
        font_big = pygame.font.Font(None, 100)
        text_surf = font_big.render(self.result_text, True, self.color)
        text_rect = text_surf.get_rect(center=(w // 2, h // 2 - 50))
        surface.blit(text_surf, text_rect)

        # Button
        pygame.draw.rect(surface, (60, 60, 80), self.btn_rect, border_radius=8)
        pygame.draw.rect(
            surface, (200, 200, 200), self.btn_rect, width=2, border_radius=8
        )

        font_small = pygame.font.Font(None, 36)
        btn_text = font_small.render("Exit Game", True, (255, 255, 255))
        btn_rect = btn_text.get_rect(center=self.btn_rect.center)
        surface.blit(btn_text, btn_rect)
