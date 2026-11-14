import math

import pygame

from settings import BG, CYAN, MUTED, PANEL, WHITE, YELLOW


class Menu:
    def __init__(self):
        self.fonts = {
            "small": pygame.font.Font(None, 24),
            "body": pygame.font.Font(None, 30),
            "button": pygame.font.Font(None, 34),
            "heading": pygame.font.Font(None, 54),
            "title": pygame.font.Font(None, 112),
        }
        self.buttons = []

    def _label(self, surface, value, font, color, position):
        image = font.render(str(value), True, color)
        surface.blit(image, image.get_rect(center=position))

    def _button(self, surface, label, action, center, width=260, active=True):
        rect = pygame.Rect(0, 0, width, 54)
        rect.center = center
        fill = (16, 37, 72) if active else (14, 23, 43)
        edge = CYAN if active else (53, 75, 110)
        pygame.draw.rect(surface, fill, rect, border_radius=14)
        pygame.draw.rect(surface, edge, rect, 2, border_radius=14)
        self._label(surface, label, self.fonts["button"], WHITE, rect.center)
        self.buttons.append((rect, action))

    def _panel(self, surface, title, subtitle=None):
        panel = pygame.Rect(290, 190, 420, 435)
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((2, 5, 15, 185))
        surface.blit(shade, (0, 0))
        pygame.draw.rect(surface, PANEL, panel, border_radius=24)
        pygame.draw.rect(surface, (49, 112, 174), panel, 2, border_radius=24)
        self._label(surface, title, self.fonts["heading"], WHITE, (500, 247))
        if subtitle:
            self._label(surface, subtitle, self.fonts["small"], MUTED, (500, 290))

    def draw(self, surface, state, time_s, score=0, best=0, level=1, volume=0.65):
        self.buttons = []
        if state in ("menu", "settings"):
            self._draw_backdrop(surface, time_s)
        if state == "menu":
            self._draw_title(surface, time_s)
            self._button(surface, "PLAY", "play", (500, 485), 250)
            self._button(surface, "SETTINGS", "settings", (500, 552), 250)
            self._button(surface, "QUIT", "quit", (500, 619), 250)
            self._label(surface, "WASD / ARROWS  •  P / ESC TO PAUSE",
                        self.fonts["small"], MUTED, (500, 724))
        elif state == "settings":
            self._panel(surface, "SETTINGS", "Adjust sound and return to the maze")
            self._label(surface, "MASTER VOLUME", self.fonts["body"], WHITE, (500, 370))
            track = pygame.Rect(385, 400, 230, 8)
            pygame.draw.rect(surface, (46, 65, 98), track, border_radius=4)
            fill = track.copy()
            fill.width = round(track.width * volume)
            pygame.draw.rect(surface, CYAN, fill, border_radius=4)
            pygame.draw.circle(surface, WHITE, (track.left + fill.width, track.centery), 10)
            self.buttons.append((pygame.Rect(365, 378, 270, 48), "volume"))
            self._label(surface, f"{round(volume * 100)}%", self.fonts["small"],
                        MUTED, (500, 440))
            self._button(surface, "BACK", "back", (500, 548))
            self._label(surface, "All sounds are generated in-game.",
                        self.fonts["small"], MUTED, (500, 602))
        elif state == "paused":
            self._panel(surface, "PAUSED", f"SCORE  {score:,}     LEVEL  {level}")
            self._button(surface, "RESUME", "resume", (500, 355))
            self._button(surface, "RESTART", "restart", (500, 423))
            self._button(surface, "SETTINGS", "settings", (500, 491))
            self._button(surface, "MAIN MENU", "menu", (500, 559))
        elif state == "game_over":
            self._panel(surface, "GAME OVER", f"FINAL SCORE  {score:,}")
            self._label(surface, f"BEST  {best:,}", self.fonts["body"], YELLOW, (500, 338))
            self._button(surface, "RETRY", "retry", (500, 438))
            self._button(surface, "MAIN MENU", "menu", (500, 512))
        elif state == "level_complete":
            self._panel(surface, "LEVEL COMPLETED", f"LEVEL {level}  •  SCORE {score:,}")
            colors = (YELLOW, CYAN, (255, 112, 190), (126, 235, 155))
            for index in range(12):
                side = 330 if index % 2 == 0 else 670
                x = side + round(math.sin(time_s * 2 + index) * 13)
                y = 326 + (index * 17 + int(time_s * 34)) % 92
                radius = 1 + round((1 + math.sin(time_s * 4 + index)) * 1.5)
                pygame.draw.circle(surface, colors[index % len(colors)],
                                   (x, y), radius)
            self._label(surface, "The maze is yours.", self.fonts["body"], YELLOW, (500, 360))
            self._button(surface, "NEXT LEVEL", "next", (500, 450))
            self._button(surface, "MAIN MENU", "menu", (500, 524))
        return self.buttons

    def _draw_backdrop(self, surface, time_s):
        surface.fill(BG)
        for index in range(72):
            x = (index * 173 + int(time_s * (7 + index % 4))) % surface.get_width()
            y = (index * 97) % surface.get_height()
            brightness = 85 + int(55 * (0.5 + 0.5 * math.sin(time_s * 1.7 + index)))
            pygame.draw.circle(surface, (28, brightness, min(255, brightness + 70)),
                               (x, y), 1 if index % 4 else 2)

    def _draw_title(self, surface, time_s):
        title = self.fonts["title"].render("PAC-MAN", True, YELLOW)
        title_rect = title.get_rect(center=(500, 275 + round(math.sin(time_s * 2) * 5)))
        glow = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        glow.blit(title, (0, 0))
        for offset in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            surface.blit(glow, title_rect.move(*offset), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(title, title_rect)
        self._label(surface, "THE NEON MAZE", self.fonts["body"], CYAN, (500, 345))
