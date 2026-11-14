import math

import pygame

from maze import DIRECTIONS
from settings import MAZE_LEFT, MAZE_TOP, TILE, YELLOW


class Player:
    def __init__(self, cell, speed):
        self.cell = cell
        self.pos = self.center(cell)
        self.direction = "left"
        self.wanted_direction = None
        self.speed = speed
        self.radius = TILE * 0.36
        self.animation = 0.0
        self.invulnerable = 0.0

    @staticmethod
    def center(cell):
        return pygame.Vector2(MAZE_LEFT + (cell[0] + 0.5) * TILE,
                              MAZE_TOP + (cell[1] + 0.5) * TILE)

    def update(self, dt, maze):
        self.animation += dt * 10
        self.invulnerable = max(0.0, self.invulnerable - dt)
        remaining = self.speed * dt
        for _ in range(4):
            if remaining <= 0:
                break
            if self.pos.distance_to(self.center(self.cell)) < 0.5:
                self.pos = self.center(self.cell)
                options = dict(maze.neighbors(self.cell))
                if self.wanted_direction in options:
                    self.direction = self.wanted_direction
                if self.direction not in options:
                    self.direction = None
                    break
                next_cell = options[self.direction]
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
        return self.cell

    def draw(self, surface):
        if self.invulnerable > 0 and int(self.invulnerable * 12) % 2:
            return
        direction_angles = {"right": 0, "down": 90, "left": 180, "up": 270}
        angle = math.radians(direction_angles.get(self.direction, 0))
        mouth = 0.12 + 0.28 * abs(math.sin(self.animation))
        start, end = angle + mouth, angle + math.tau - mouth
        points = [self.pos]
        points.extend(
            (self.pos.x + math.cos(start + (end - start) * i / 32) * self.radius,
             self.pos.y + math.sin(start + (end - start) * i / 32) * self.radius)
            for i in range(33)
        )
        pygame.draw.polygon(surface, YELLOW, points)
        pygame.draw.circle(surface, (255, 244, 154), self.pos, self.radius, 2)
