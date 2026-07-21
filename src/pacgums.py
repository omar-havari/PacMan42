"""The pac-gums for a level: where they are, their type, and eating them.

:class:`PacgumManager` owns every pac-gum so :class:`~src.GameDemo.GameDemo`
only has to ask "what did Pac-Man just eat?" and "how many are left?".
"""
import os
from typing import Dict, List, Optional, Tuple

import pygame

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

Cell = Tuple[int, int]


class PacgumManager:
    """Tracks and draws every pac-gum and super-pac-gum in one level."""

    DOT_COLOR = (255, 183, 174)  # the classic pale-pink arcade dot

    def __init__(
        self,
        grid: List[List[str]],
        start_cell: Cell,
        cell: int,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Place a pac-gum in every corridor (bar the player's start cell).

        Four corners get a super-pac-gum instead. Positions are stored in a
        dict (not written into the grid) so eating one is a single ``pop`` and
        counting the rest is a single ``len`` - and the grid stays purely about
        walls.
        """
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        # (row, col) -> "PACGUM" or "SUPER".
        self.pacgums: Dict[Cell, str] = {}
        rows = len(grid)
        cols = len(grid[0])

        # A small pac-gum in every corridor cell except the player's start.
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "CORRIDOR" and (r, c) != start_cell:
                    self.pacgums[(r, c)] = "PACGUM"

        # One super-pac-gum in each of the 4 corners. The expanded grid puts
        # corridors on every odd row/column index, so these corner cells are
        # guaranteed to exist - no searching needed.
        corners: List[Cell] = [
            (1, 1),
            (1, cols - 2),
            (rows - 2, 1),
            (rows - 2, cols - 2),
        ]
        for corner in corners:
            if corner in self.pacgums:
                self.pacgums[corner] = "SUPER"

        # Total at level start, kept for the win-condition check.
        self.total = len(self.pacgums)

        # The sprites. If an image is missing we don't crash (robustness
        # requirement) - draw() falls back to plain circles instead.
        self.dot_size = max(4, cell * 2 // 3)
        self.dot_image = self._load_sprite(
            'ChatGPT Image Jul 11, 2026, 03_31_12 PM.png',
            (self.dot_size, self.dot_size)
        )
        self.super_image = self._load_sprite(
            'Screenshot_From_2026-07-10_12-32-10-removebg-preview.png',
            (cell, cell)
        )

    def _load_sprite(
        self, filename: str, size: Tuple[int, int]
    ) -> Optional[pygame.Surface]:
        """Load and scale an asset, or return ``None`` if it is missing."""
        try:
            image_path = os.path.join(_ASSETS, 'images', filename)
            image = pygame.image.load(image_path).convert_alpha()
            return pygame.transform.scale(image, size)
        except (FileNotFoundError, pygame.error):
            print(f"Warning: image '{filename}' not found, using a plain circle.")
            return None

    def remaining(self) -> int:
        """Return how many pac-gums are still uneaten."""
        return len(self.pacgums)

    def collect(self, cell_pos: Cell) -> Optional[str]:
        """Eat and remove the pac-gum at ``cell_pos``.

        Returns:
            ``"PACGUM"``, ``"SUPER"``, or ``None`` if the cell was empty.
        """
        return self.pacgums.pop(cell_pos, None)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw every remaining pac-gum (sprite, or a circle fallback)."""
        radius = max(2, self.cell // 8)
        # The cigarette is smaller than the cell, so it gets its own margin
        # to stay centred in the corridor.
        dot_margin = (self.cell - self.dot_size) // 2
        for (r, c), kind in self.pacgums.items():
            x = self.offset_x + c * self.cell
            y = self.offset_y + r * self.cell
            center = (x + self.cell // 2, y + self.cell // 2)
            if kind == "PACGUM":
                if self.dot_image:
                    screen.blit(self.dot_image, (x + dot_margin, y + dot_margin))
                else:
                    pygame.draw.circle(screen, self.DOT_COLOR, center, radius)
            else:
                if self.super_image:
                    screen.blit(self.super_image, (x, y))
                else:
                    pygame.draw.circle(screen, self.DOT_COLOR, center, radius * 3)
