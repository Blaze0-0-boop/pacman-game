from collections import deque
import random

from settings import COLS, ROWS

DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


class Maze:
    """A connected, seeded maze with a small number of extra loops."""

    def __init__(self, level=1):
        self.cols, self.rows = COLS, ROWS
        self.grid = [["#"] * self.cols for _ in range(self.rows)]
        rng = random.Random(9281 + level * 7919)
        start = (1, 1)
        self.grid[start[1]][start[0]] = " "
        stack = [start]

        while stack:
            x, y = stack[-1]
            choices = [
                (x + dx, y + dy, x + dx // 2, y + dy // 2)
                for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))
                if 1 <= x + dx < self.cols - 1 and 1 <= y + dy < self.rows - 1
                and self.grid[y + dy][x + dx] == "#"
            ]
            if not choices:
                stack.pop()
                continue
            nx, ny, wx, wy = rng.choice(choices)
            self.grid[wy][wx] = " "
            self.grid[ny][nx] = " "
            stack.append((nx, ny))

        # A few opened walls keep the maze from feeling like a single long corridor.
        walls = [
            (x, y)
            for y in range(1, self.rows - 1)
            for x in range(1, self.cols - 1)
            if self.grid[y][x] == "#"
        ]
        rng.shuffle(walls)
        for x, y in walls[:max(5, min(30, 5 + level * 2))]:
            self.grid[y][x] = " "

        self.grid[self.rows // 2][0] = " "
        self.grid[self.rows // 2][self.cols - 1] = " "
        self.player_spawn = start
        self.home = self.nearest_open((self.cols // 2, self.rows // 2))
        self.ghost_spawns = self._choose_ghost_spawns()
        self.pellets = {
            (x, y)
            for y in range(self.rows)
            for x in range(self.cols)
            if self.is_open((x, y)) and (x, y) != self.player_spawn
            and (x, y) not in self.ghost_spawns
        }
        open_cells = [(x, y) for y in range(1, self.rows - 1)
                      for x in range(1, self.cols - 1) if self.is_open((x, y))]
        self.power_pellets = set()
        power_candidates = [
            cell for cell in open_cells
            if cell != self.player_spawn and cell not in self.ghost_spawns
        ]
        for corner in ((1, 1), (self.cols - 2, 1), (1, self.rows - 2),
                       (self.cols - 2, self.rows - 2)):
            spot = min(power_candidates, key=lambda cell: self.distance(cell, corner))
            self.power_pellets.add(spot)
            power_candidates.remove(spot)
        self.pellets.difference_update(self.power_pellets)

    def is_open(self, cell):
        x, y = cell
        return 0 <= x < self.cols and 0 <= y < self.rows and self.grid[y][x] != "#"

    def neighbors(self, cell):
        x, y = cell
        for name, (dx, dy) in DIRECTIONS.items():
            nx, ny = x + dx, y + dy
            if y == self.rows // 2 and nx < 0:
                nx = self.cols - 1
            elif y == self.rows // 2 and nx >= self.cols:
                nx = 0
            if self.is_open((nx, ny)):
                yield name, (nx, ny)

    def nearest_open(self, cell):
        open_cells = [(x, y) for y in range(self.rows) for x in range(self.cols)
                      if self.is_open((x, y))]
        return min(open_cells, key=lambda point: self.distance(point, cell))

    def _distances(self, start):
        distances = {start: 0}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for _, nxt in self.neighbors(current):
                if nxt not in distances:
                    distances[nxt] = distances[current] + 1
                    queue.append(nxt)
        return distances

    def _choose_ghost_spawns(self):
        distances = self._distances(self.player_spawn)
        ordered = sorted(distances, key=lambda cell: distances[cell], reverse=True)
        chosen = []
        for cell in ordered:
            if all(self.distance(cell, other) >= 2 for other in chosen):
                chosen.append(cell)
            if len(chosen) == 4:
                break
        while len(chosen) < 4:
            chosen.append(self.home)
        return chosen

    @staticmethod
    def distance(first, second):
        return abs(first[0] - second[0]) + abs(first[1] - second[1])
