import json
import math
import random
import sys

import pygame

from audio import Audio
from ghost import GHOSTS, Ghost
from maze import Maze
from menu import Menu
from player import Player
from settings import (
    BG, COLS, CYAN, DATA_DIR, FPS, HEIGHT, MAZE_LEFT, MAZE_TOP, MUTED,
    PANEL, ROWS, SCORES_FILE, SETTINGS_FILE, TILE, WHITE, WIDTH, YELLOW,
)

MODE_CYCLE = (("scatter", 7.0), ("chase", 20.0), ("scatter", 7.0),
              ("chase", 20.0), ("scatter", 5.0), ("chase", 20.0))


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("PAC-MAN — Neon Maze")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 56)
        self.menu = Menu()
        self.audio = Audio()
        self.volume = 0.65
        self.best = 0
        self._load_data()
        self.audio.set_volume(self.volume)
        self.state = "menu"
        self.score = 0
        self.level = 1
        self.lives = 3
        self.elapsed = 0.0
        self.mode_elapsed = 0.0
        self.frightened_left = 0.0
        self.ghost_chain = 0
        self.particles = []
        self.floaters = []
        self._build_level()
        self.running = True
        self.buttons = []

    def _load_data(self):
        try:
            with SCORES_FILE.open(encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                self.best = max(0, int(data.get("best", 0)))
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            print(f"Could not load score data: {exc}", file=sys.stderr)
        try:
            with SETTINGS_FILE.open(encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                self.volume = max(0.0, min(1.0, float(data.get("volume", 0.65))))
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError) as exc:
            print(f"Could not load settings: {exc}", file=sys.stderr)

    def _save_data(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        for path, data in ((SCORES_FILE, {"best": self.best}),
                           (SETTINGS_FILE, {"volume": self.volume})):
            try:
                with path.open("w", encoding="utf-8") as file:
                    json.dump(data, file, indent=2)
            except OSError as exc:
                print(f"Could not save {path.name}: {exc}", file=sys.stderr)

    def _build_level(self):
        self.maze = Maze(self.level)
        self.player = Player(self.maze.player_spawn, 112 + min(self.level - 1, 5) * 4)
        self.ghosts = []
        for index, (name, color, scatter_target) in enumerate(GHOSTS):
            speed = 91 + min(self.level - 1, 6) * 5 + index * 2
            self.ghosts.append(Ghost(name, color, self.maze.ghost_spawns[index],
                                     scatter_target, self.maze, speed, index))
        self.elapsed = 0.0
        self.mode_elapsed = 0.0
        self.frightened_left = 0.0
        self.ghost_chain = 0
        self.particles = []
        self.floaters = []

    def _start_game(self, fresh=True):
        if fresh:
            self.score = 0
            self.level = 1
            self.lives = 3
        self._build_level()
        self.state = "playing"
        self.audio.start_music()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.04)
            self.elapsed += dt
            self._events()
            if self.state == "playing":
                self._update(dt)
            self._draw()
            pygame.display.flip()
        self._save_data()
        pygame.quit()

    def _events(self):
        scale = min(self.screen.get_width() / WIDTH, self.screen.get_height() / HEIGHT)
        offset_x = (self.screen.get_width() - WIDTH * scale) / 2
        offset_y = (self.screen.get_height() - HEIGHT * scale) / 2
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self._key_down(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for rect, action in self.buttons:
                    if rect.collidepoint(pos):
                        if action == "volume":
                            logical_x = (pos[0] - offset_x) / scale
                            self.volume = max(0.0, min(1.0, (logical_x - 385) / 230))
                            self.audio.set_volume(self.volume)
                            self._save_data()
                        else:
                            self._action(action)
                        break
            elif event.type == pygame.MOUSEMOTION and self.state == "settings":
                if pygame.mouse.get_pressed()[0] and self.buttons:
                    for rect, action in self.buttons:
                        if action == "volume" and rect.collidepoint(event.pos):
                            x = (event.pos[0] - offset_x) / scale
                            self.volume = max(0.0, min(1.0, (x - 385) / 230))
                            self.audio.set_volume(self.volume)

    def _key_down(self, key):
        if self.state == "playing":
            directions = {pygame.K_UP: "up", pygame.K_w: "up",
                          pygame.K_DOWN: "down", pygame.K_s: "down",
                          pygame.K_LEFT: "left", pygame.K_a: "left",
                          pygame.K_RIGHT: "right", pygame.K_d: "right"}
            if key in directions:
                self.player.wanted_direction = directions[key]
            elif key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
        elif key in (pygame.K_ESCAPE, pygame.K_p) and self.state == "paused":
            self.state = "playing"
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.state == "menu":
                self._action("play")
            elif self.state == "paused":
                self._action("resume")
            elif self.state == "game_over":
                self._action("retry")
            elif self.state == "level_complete":
                self._action("next")
        elif key == pygame.K_ESCAPE and self.state == "settings":
            self._action("back")

    def _action(self, action):
        if action == "play" or action == "retry" or action == "restart":
            self._start_game(fresh=True)
        elif action == "resume":
            self.state = "playing"
        elif action == "settings":
            self.settings_return = self.state
            self.state = "settings"
        elif action == "back":
            self.state = getattr(self, "settings_return", "menu")
        elif action == "menu":
            self.state = "menu"
        elif action == "next":
            self.level += 1
            self._build_level()
            self.state = "playing"
        elif action == "quit":
            self.running = False

    def _update(self, dt):
        self.elapsed += 0
        self.mode_elapsed += dt
        self.frightened_left = max(0, self.frightened_left - dt)
        if self.frightened_left == 0:
            self.ghost_chain = 0
            for ghost in self.ghosts:
                if ghost.state == "frightened":
                    ghost.state = "normal"
        self.player.update(dt, self.maze)
        mode = self._mode()
        ghost_speed_factor = 1 + min(self.level - 1, 8) * 0.045
        for ghost in self.ghosts:
            ghost.update(dt, self.maze, self.player, self.ghosts, mode,
                         ghost.base_speed * ghost_speed_factor)

        if self.player.cell in self.maze.pellets:
            self.maze.pellets.remove(self.player.cell)
            self.score += 10
            self.audio.play("dot")
            self._burst(self.player.pos, (117, 207, 255), 3)
        if self.player.cell in self.maze.power_pellets:
            self.maze.power_pellets.remove(self.player.cell)
            self.score += 50
            self.frightened_left = max(6.5, 9.0 - self.level * 0.35)
            self.ghost_chain = 0
            self.audio.play("power")
            for ghost in self.ghosts:
                if ghost.state != "eaten":
                    ghost.state = "frightened"
            self._burst(self.player.pos, YELLOW, 18)
        self.best = max(self.best, self.score)

        for ghost in self.ghosts:
            if self.player.pos.distance_to(ghost.pos) < TILE * 0.7:
                if ghost.state == "frightened":
                    ghost.state = "eaten"
                    points = 200 * (2 ** min(self.ghost_chain, 3))
                    self.ghost_chain += 1
                    self.score += points
                    self.best = max(self.best, self.score)
                    self.audio.play("eat")
                    self._float_text(f"+{points}", ghost.pos)
                    self._burst(ghost.pos, (120, 194, 255), 14)
                elif ghost.state != "eaten" and self.player.invulnerable <= 0:
                    self._lose_life()
                    break

        for particle in self.particles:
            particle["pos"] += particle["velocity"] * dt
            particle["life"] -= dt
        self.particles = [particle for particle in self.particles if particle["life"] > 0]
        for floater in self.floaters:
            floater["pos"].y -= 30 * dt
            floater["life"] -= dt
        self.floaters = [floater for floater in self.floaters if floater["life"] > 0]

        if not self.maze.pellets and not self.maze.power_pellets:
            self.state = "level_complete"
            self.audio.play("win")
            self._save_data()

    def _mode(self):
        remaining = self.mode_elapsed
        for mode, duration in MODE_CYCLE:
            if remaining < duration:
                return "frightened" if self.frightened_left > 0 else mode
            remaining -= duration
        return "frightened" if self.frightened_left > 0 else "chase"

    def _lose_life(self):
        self.lives -= 1
        self.audio.play("death")
        self._burst(self.player.pos, YELLOW, 24)
        if self.lives <= 0:
            self.best = max(self.best, self.score)
            self._save_data()
            self.state = "game_over"
            return
        self.player = Player(self.maze.player_spawn, self.player.speed)
        for index, ghost in enumerate(self.ghosts):
            ghost.cell = self.maze.ghost_spawns[index]
            ghost.pos = ghost.center(ghost.cell)
            ghost.state = "normal"
            ghost.direction = "left"
        self.frightened_left = 0

    def _burst(self, pos, color, count):
        for _ in range(count):
            angle = random.random() * math.tau
            speed = random.uniform(24, 115)
            self.particles.append({
                "pos": pygame.Vector2(pos),
                "velocity": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "life": random.uniform(0.18, 0.55),
                "max_life": 0.55,
                "color": color,
                "radius": random.randint(2, 4),
            })

    def _float_text(self, text, pos):
        self.floaters.append({"text": text, "pos": pygame.Vector2(pos), "life": 0.85})

    def _draw(self):
        self.canvas.fill(BG)
        self._draw_stars()
        if self.state in ("playing", "paused", "game_over", "level_complete"):
            self._draw_hud()
            self._draw_maze()
            self._draw_pellets()
            for particle in self.particles:
                alpha = max(0, min(255, int(255 * particle["life"] /
                                            particle["max_life"])))
                pygame.draw.circle(self.canvas, particle["color"],
                                   (round(particle["pos"].x), round(particle["pos"].y)),
                                   particle["radius"] if alpha > 70 else 1)
            for ghost in self.ghosts:
                ghost.draw(self.canvas, self.frightened_left)
            self.player.draw(self.canvas)
            for floater in self.floaters:
                image = self.font.render(floater["text"], True, YELLOW)
                image.set_alpha(round(255 * min(1, floater["life"] / 0.3)))
                self.canvas.blit(image, image.get_rect(center=floater["pos"]))
        self.buttons = self.menu.draw(self.canvas, self.state, self.elapsed,
                                      self.score, self.best, self.level, self.volume)
        size = self.screen.get_size()
        scale = min(size[0] / WIDTH, size[1] / HEIGHT)
        scaled = pygame.transform.smoothscale(
            self.canvas, (round(WIDTH * scale), round(HEIGHT * scale)))
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, ((size[0] - scaled.get_width()) // 2,
                                  (size[1] - scaled.get_height()) // 2))
        offset_x = (size[0] - scaled.get_width()) // 2
        offset_y = (size[1] - scaled.get_height()) // 2
        self.buttons = [
            (pygame.Rect(offset_x + round(rect.x * scale),
                         offset_y + round(rect.y * scale),
                         round(rect.width * scale), round(rect.height * scale)), action)
            for rect, action in self.buttons
        ]

    def _draw_stars(self):
        for index in range(34):
            x = (index * 193 + int(self.elapsed * (4 + index % 3))) % WIDTH
            y = (index * 137 + 17) % HEIGHT
            brightness = 30 + int(38 * (0.5 + 0.5 * math.sin(self.elapsed + index)))
            self.canvas.set_at((x, y), (brightness, brightness + 7, brightness + 28))

    def _draw_hud(self):
        pygame.draw.rect(self.canvas, PANEL, (0, 0, WIDTH, 112))
        self._text("SCORE", (66, 24), CYAN, self.small_font)
        self._text(f"{self.score:06d}", (66, 50), WHITE, self.font)
        self._text("BEST", (268, 24), CYAN, self.small_font)
        self._text(f"{self.best:06d}", (268, 50), WHITE, self.font)
        self._text(f"LEVEL  {self.level}", (493, 42), YELLOW, self.font)
        self._text("LIVES", (748, 24), CYAN, self.small_font)
        for life in range(max(0, self.lives)):
            pygame.draw.circle(self.canvas, YELLOW, (766 + life * 32, 63), 11)
            pygame.draw.polygon(self.canvas, PANEL,
                                [(766 + life * 32, 63), (779 + life * 32, 56),
                                 (779 + life * 32, 70)])
        self._text("P / ESC  PAUSE", (900, 48), MUTED, self.small_font)

    def _draw_maze(self):
        rect = pygame.Rect(MAZE_LEFT - 12, MAZE_TOP - 12,
                           COLS * TILE + 24, ROWS * TILE + 24)
        pygame.draw.rect(self.canvas, (7, 15, 37), rect, border_radius=18)
        for y, row in enumerate(self.maze.grid):
            for x, tile in enumerate(row):
                if tile == "#":
                    cell = pygame.Rect(MAZE_LEFT + x * TILE + 2,
                                       MAZE_TOP + y * TILE + 2, TILE - 4, TILE - 4)
                    pygame.draw.rect(self.canvas, (16, 38, 77), cell, border_radius=6)
                    pygame.draw.rect(self.canvas, (40, 106, 183), cell, 1, border_radius=6)
                    pygame.draw.line(self.canvas, (66, 157, 224),
                                     (cell.left + 5, cell.top + 2),
                                     (cell.right - 5, cell.top + 2), 1)
        pygame.draw.rect(self.canvas, (52, 141, 215), rect, 2, border_radius=18)

    def _draw_pellets(self):
        for x, y in self.maze.pellets:
            center = (MAZE_LEFT + x * TILE + TILE // 2,
                      MAZE_TOP + y * TILE + TILE // 2)
            pygame.draw.circle(self.canvas, (68, 148, 225), center, 5)
            pygame.draw.circle(self.canvas, (220, 241, 255), center, 2)
        pulse = 7 + round(2 * math.sin(self.elapsed * 5))
        for x, y in self.maze.power_pellets:
            center = (MAZE_LEFT + x * TILE + TILE // 2,
                      MAZE_TOP + y * TILE + TILE // 2)
            pygame.draw.circle(self.canvas, (255, 166, 42), center, pulse + 4, 2)
            pygame.draw.circle(self.canvas, YELLOW, center, pulse)
            pygame.draw.circle(self.canvas, WHITE, center, 3)

    def _text(self, value, position, color, font):
        self.canvas.blit(font.render(str(value), True, color), position)
