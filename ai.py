import heapq
import random

from maze import DIRECTIONS, OPPOSITE


def astar(maze, start, goal):
    """Return a shortest sequence of direction names between two maze cells."""
    if not maze.is_open(goal):
        goal = maze.nearest_open(goal)
    frontier = [(0, start)]
    previous = {start: None}
    costs = {start: 0}
    while frontier:
        _, current = heapq.heappop(frontier)
        if current == goal:
            break
        for direction, nxt in maze.neighbors(current):
            cost = costs[current] + 1
            if cost < costs.get(nxt, float("inf")):
                costs[nxt] = cost
                horizontal = abs(nxt[0] - goal[0])
                horizontal = min(horizontal, maze.cols - horizontal)
                priority = cost + horizontal + abs(nxt[1] - goal[1])
                heapq.heappush(frontier, (priority, nxt))
                previous[nxt] = (current, direction)
    if goal not in previous:
        return []
    path = []
    current = goal
    while current != start:
        parent, direction = previous[current]
        path.append(direction)
        current = parent
    return list(reversed(path))


class GhostAI:
    def __init__(self, name, maze, rng=None):
        self.name = name
        self.maze = maze
        self.rng = rng or random.Random()

    def choose_direction(self, ghost, player, ghosts, mode):
        options = list(self.maze.neighbors(ghost.cell))
        if not options:
            return None

        if ghost.state == "eaten":
            target = self.maze.home
        elif mode == "frightened":
            return self._flee_direction(options, player.cell, ghost.direction)
        elif mode == "scatter":
            target = ghost.scatter_target
        else:
            target = self._chase_target(ghost, player, ghosts)

        path = astar(self.maze, ghost.cell, target)
        if path:
            desired = path[0]
            if desired != OPPOSITE.get(ghost.direction) or len(options) == 1:
                return desired
        return self._fallback(options, ghost.direction, player.cell)

    def _chase_target(self, ghost, player, ghosts):
        if self.name == "pinky":
            dx, dy = DIRECTIONS.get(player.direction, (0, 0))
            return self._clamp((player.cell[0] + dx * 4, player.cell[1] + dy * 4))
        if self.name == "inky":
            blinky = next((other for other in ghosts if other.name == "blinky"), None)
            pivot = blinky.cell if blinky else ghost.cell
            dx, dy = DIRECTIONS.get(player.direction, (0, 0))
            ahead = (player.cell[0] + dx * 2, player.cell[1] + dy * 2)
            return self._clamp((ahead[0] + ahead[0] - pivot[0],
                                ahead[1] + ahead[1] - pivot[1]))
        if self.name == "clyde" and self.maze.distance(ghost.cell, player.cell) < 7:
            return ghost.scatter_target
        return player.cell

    def _clamp(self, cell):
        return max(1, min(self.maze.cols - 2, cell[0])), max(
            1, min(self.maze.rows - 2, cell[1]))

    def _flee_direction(self, options, player_cell, current_direction):
        candidates = [item for item in options
                      if item[0] != OPPOSITE.get(current_direction)] or options
        distances = [(self.maze.distance(cell, player_cell), direction)
                     for direction, cell in candidates]
        best = max(distance for distance, _ in distances)
        return self.rng.choice([direction for distance, direction in distances
                                if distance == best])

    @staticmethod
    def _fallback(options, current_direction, player_cell):
        candidates = [item for item in options
                      if item[0] != OPPOSITE.get(current_direction)] or options
        return min(candidates, key=lambda item: (
            abs(item[1][0] - player_cell[0]) + abs(item[1][1] - player_cell[1])
        ))[0]
