import math

import pygame

from ai import GhostAI
from settings import MAZE_LEFT, MAZE_TOP, TILE

GHOSTS = (
    ("blinky", (255, 72, 92), (23, 1)),
    ("pinky", (255, 112, 190), (1, 19)),
    ("inky", (68, 220, 244), (23, 19)),
    ("clyde", (255, 165, 69), (1, 1)),
)


class Ghost:
    def __init__(self, name, color, cell, scatter_target, maze, speed, seed):
        self.name = name
        self.color = color
        self.cell = cell
        self.pos = self.center(cell)
        self.direction = "left"
        self.scatter_target = scatter_target
        self.state = "normal"
        self.base_speed = speed
        self.speed = speed
        self.animation = seed * 0.7
        self.ai = GhostAI(name, maze)
        self.seed = seed

    @staticmethod
    def center(cell):
        return pygame.Vector2(MAZE_LEFT + (cell[0] + 0.5) * TILE,
                              MAZE_TOP + (cell[1] + 0.5) * TILE)

    def update(self, dt, maze, player, ghosts, mode, speed):
        self.animation += dt * 7
        self.speed = speed * (0.72 if self.state == "frightened" else
                              1.2 if self.state == "eaten" else 1)
        remaining = self.speed * dt
        for _ in range(4):
            if remaining <= 0:
                break
            if self.pos.distance_to(self.center(self.cell)) < 0.5:
                self.pos = self.center(self.cell)
                if self.state == "eaten" and self.cell == maze.home:
                    self.state = "normal"
                effective_mode = "frightened" if self.state == "frightened" else mode
                direction = self.ai.choose_direction(self, player, ghosts, effective_mode)
                options = dict(maze.neighbors(self.cell))
                if direction not in options:
                    direction = next(iter(options), None)
                if direction is None:
                    break
                self.direction = direction
                next_cell = options[direction]
                target = self.center(next_cell)
                if abs(target.x - self.pos.x) > TILE * 1.5:
                    self.cell = next_cell
                    self.pos = target
                    continue
            else:
                next_cell = dict(maze.neighbors(self.cell)).get(self.direction)
                if next_cell is None:
                    break
                target = self.center(next_cell)
            distance = self.pos.distance_to(target)
            step = min(remaining, distance)
            if distance:
                self.pos += (target - self.pos) * (step / distance)
            remaining -= step
            if distance <= step + 0.01:
                self.cell = next_cell
                self.pos = target

    def draw(self, surface, frightened_left=0):
        x, y = round(self.pos.x), round(self.pos.y)
        radius = TILE * 0.42
        if self.state == "eaten":
            eye_color = (245, 248, 255)
            for offset in (-5, 5):
                pygame.draw.circle(surface, eye_color, (x + offset, y - 2), 5)
                pygame.draw.circle(surface, (42, 105, 232), (x + offset, y - 2), 2)
            return

        frightened = self.state == "frightened"
        color = ((255, 255, 255) if frightened and frightened_left < 2
                 and int(frightened_left * 8) % 2 else
                 (58, 103, 255) if frightened else self.color)
        pygame.draw.circle(surface, color, (x, y - 2), int(radius))
        body_rect = pygame.Rect(x - radius, y - 2, radius * 2, radius)
        pygame.draw.rect(surface, color, body_rect)
        foot_y = y + int(radius * 0.72)
        for index in range(4):
            foot_x = x - radius + (index + 0.5) * radius * 0.5
            wobble = 2 * math.sin(self.animation + index * 1.5)
            pygame.draw.circle(surface, color, (round(foot_x), round(foot_y + wobble)),
                               int(radius * 0.25))
        if frightened:
            eye_y = y + 1
            for eye_x in (x - 5, x + 5):
                pygame.draw.circle(surface, (248, 250, 255), (eye_x, eye_y), 2)
            pygame.draw.line(surface, (248, 250, 255), (x - 7, y + 8), (x + 7, y + 8), 2)
        else:
            for eye_x in (x - 5, x + 5):
                pygame.draw.ellipse(surface, (255, 255, 255), (eye_x - 4, y - 6, 8, 10))
                dx, dy = {"left": (-2, 0), "right": (2, 0), "up": (0, -2),
                          "down": (0, 2)}.get(self.direction, (0, 0))
                pygame.draw.circle(surface, (26, 55, 152), (eye_x + dx, y - 2 + dy), 2)
