import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from ai import astar
from game import Game
from maze import Maze


class MazeTests(unittest.TestCase):
    def test_level_layouts_are_connected_and_have_four_power_pellets(self):
        for level in range(1, 9):
            with self.subTest(level=level):
                maze = Maze(level)
                reachable = {maze.player_spawn}
                pending = [maze.player_spawn]
                while pending:
                    current = pending.pop()
                    for _, neighbor in maze.neighbors(current):
                        if neighbor not in reachable:
                            reachable.add(neighbor)
                            pending.append(neighbor)
                open_cells = {(x, y) for y in range(maze.rows)
                              for x in range(maze.cols) if maze.is_open((x, y))}
                self.assertEqual(open_cells, reachable)
                self.assertTrue(maze.pellets)
                self.assertEqual(len(maze.power_pellets), 4)

    def test_astar_returns_a_shortest_valid_path(self):
        maze = Maze(2)
        start, goal = maze.player_spawn, maze.ghost_spawns[0]
        path = astar(maze, start, goal)
        self.assertTrue(path)
        cell = start
        for direction in path:
            options = dict(maze.neighbors(cell))
            self.assertIn(direction, options)
            cell = options[direction]
        self.assertEqual(cell, goal)
        distances = {start: 0}
        pending = [start]
        while pending:
            current = pending.pop(0)
            for _, neighbor in maze.neighbors(current):
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    pending.append(neighbor)
        self.assertEqual(len(path), distances[goal])


class GameplayTests(unittest.TestCase):
    def test_dots_power_pellets_ghosts_and_death(self):
        game = Game()
        game._start_game()
        for ghost in game.ghosts:
            ghost.state = "eaten"
            ghost.pos = pygame.Vector2(-100, -100)

        pellet = next(iter(game.maze.pellets))
        game.player.cell = pellet
        game.player.pos = game.player.center(pellet)
        game._update(0)
        self.assertEqual(game.score, 10)
        self.assertNotIn(pellet, game.maze.pellets)

        power = next(iter(game.maze.power_pellets))
        game.player.cell = power
        game.player.pos = game.player.center(power)
        game._update(0)
        self.assertGreater(game.frightened_left, 0)
        self.assertNotIn(power, game.maze.power_pellets)

        ghost = game.ghosts[0]
        ghost.state = "frightened"
        ghost.pos = pygame.Vector2(game.player.pos)
        game._update(0)
        self.assertEqual(ghost.state, "eaten")
        self.assertEqual(game.score, 260)

        ghost.state = "normal"
        ghost.pos = pygame.Vector2(game.player.pos)
        game._update(0)
        self.assertEqual(game.lives, 2)

    def test_best_score_and_volume_are_persisted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            with patch("game.DATA_DIR", data_dir), \
                    patch("game.SCORES_FILE", data_dir / "scores.json"), \
                    patch("game.SETTINGS_FILE", data_dir / "settings.json"):
                game = Game()
                game.best = 1840
                game.volume = 0.35
                game._save_data()
                loaded = Game()
                self.assertEqual(loaded.best, 1840)
                self.assertAlmostEqual(loaded.volume, 0.35)


if __name__ == "__main__":
    pygame.init()
    unittest.main()
