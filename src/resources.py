"""Resolve on-disk resource paths for both source and packaged (frozen) runs.

When the game runs from source, data files live next to the project root. When
it runs as a PyInstaller bundle, they are unpacked into ``sys._MEIPASS``. This
module hides that difference so every asset lookup works in both cases.
"""
import os
import sys


def base_path() -> str:
    """Return the directory that contains ``assets/`` and ``config.json``.

    Frozen (PyInstaller) builds expose the bundled data under ``sys._MEIPASS``;
    a normal source checkout uses the project root (the parent of ``src/``).
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass is not None:
            return str(meipass)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_dir() -> str:
    """Absolute path to the bundled ``assets/`` directory."""
    return os.path.join(base_path(), "assets")


def default_config_path() -> str:
    """Absolute path to the bundled default ``config.json``."""
    return os.path.join(base_path(), "config.json")
