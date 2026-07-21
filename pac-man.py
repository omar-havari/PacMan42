"""Command-line entry point: validate the args and launch the game.

Usage::

    python pac-man.py config.json
"""
import sys

from src.config import Config
from src.app import run_game


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].endswith(".json"):
        print("Usage: python pac-man.py config.json")
        sys.exit(1)

    config_file_path = sys.argv[1]
    config = Config(config_file_path)
    # Task 8.1: hand off to the single GameState-driven main loop.
    run_game(config)
