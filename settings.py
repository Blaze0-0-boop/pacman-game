from pathlib import Path

WIDTH = 1000
HEIGHT = 800
FPS = 60
TILE = 28
COLS = 25
ROWS = 21
MAZE_LEFT = (WIDTH - COLS * TILE) // 2
MAZE_TOP = 142

BG = (5, 9, 25)
PANEL = (10, 18, 42)
WHITE = (235, 243, 255)
MUTED = (126, 151, 190)
CYAN = (53, 197, 255)
YELLOW = (255, 215, 54)

DATA_DIR = Path(__file__).resolve().parent / "data"
SCORES_FILE = DATA_DIR / "scores.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
