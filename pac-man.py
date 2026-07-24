"""Command-line entry point: validate the args and launch the game.

Usage::

    python pac-man.py config.json

If no argument is given (for example when launched from a packaged build by
double-click), the bundled default ``config.json`` is used instead.
"""
import sys

from src.config import Config
from src.app import run_game
from src.resources import default_config_path


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No argument (e.g. launched from Itch.io by double-click): use the
        # bundled default config that ships inside the package.
        config_file_path = default_config_path()
    elif len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        config_file_path = sys.argv[1]
    else:
        print("Usage: python pac-man.py [config.json]")
        sys.exit(1)

    config = Config(config_file_path)
    run_game(config)
