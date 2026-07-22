"""Generating the maze grid and drawing it in the classic Pac-Man tube style.

:class:`MazeLoader` wraps the external ``mazegenerator`` package: it expands the
generator's compact output into a full WALL/CORRIDOR grid (with the hidden "42"
turned into its own solid wall type) and owns the layout math every drawable
object uses so the geometry can never disagree with the walls on screen.
"""
from typing import List, Optional, Tuple

import pygame

from mazegenerator.mazegenerator import MazeGenerator


class MazeLoader:
    """Builds and draws the expanded maze grid for a level."""

    WALL_COLOR = (33, 33, 255)
    FT_COLOR = (255, 0, 255)  # magenta for the "42" hidden in the maze
    BG_COLOR = (0, 0, 0)

    def generate(
        self, width: int, height: int, seed: int
    ) -> Optional[List[List[str]]]:
        """Generate an expanded ``(2h+1) x (2w+1)`` WALL/CORRIDOR grid.

        Args:
            width: Maze width in generator cells.
            height: Maze height in generator cells.
            seed: Seed for reproducible generation.

        Returns:
            The expanded grid, or ``None`` if generation failed (the error is
            printed rather than raised, so the caller can recover cleanly).
        """
        extended_maze = [
            ["WALL" for _ in range(width * 2 + 1)]
            for _ in range(height * 2 + 1)
        ]

        try:
            maze = MazeGenerator(
                size=(width, height),
                perfect=False,
                entry_cell=(0, 0),
                exit_cell=(-1, -1),
                seed=seed,
            )
        except Exception as e:  # noqa: BLE001 - any generator failure recovers
            print(f"Error generating maze: {e}")
            return None

        # The generator hides a "42" in the middle of every maze: those cells
        # keep the value 15 (walled on all four sides) and are never visited,
        # so 15 is a unique marker for "part of the 42". They become FT_WALL:
        # drawn in a different colour, still solid, and NOT corridors (which
        # also stops pac-gums being placed inside the sealed 42 where Pac-Man
        # could never reach them - a bug that made every level impossible).
        cells = maze.maze
        for i, row in enumerate(cells):
            for j, cell in enumerate(row):
                if cell == 15:
                    extended_maze[i * 2 + 1][j * 2 + 1] = "FT_WALL"
                    # Paint the edge cell between two neighbouring "42" cells so
                    # the digits show as connected strokes, not separate dots.
                    if j + 1 < len(row) and row[j + 1] == 15:
                        extended_maze[i * 2 + 1][j * 2 + 2] = "FT_WALL"
                    if i + 1 < len(cells) and cells[i + 1][j] == 15:
                        extended_maze[i * 2 + 2][j * 2 + 1] = "FT_WALL"
                    continue
                extended_maze[i * 2 + 1][j * 2 + 1] = "CORRIDOR"
                if cell & 1 == 0:
                    extended_maze[i * 2][j * 2 + 1] = "CORRIDOR"
                if cell & 2 == 0:
                    extended_maze[i * 2 + 1][j * 2 + 2] = "CORRIDOR"
                if cell & 4 == 0:
                    extended_maze[i * 2 + 2][j * 2 + 1] = "CORRIDOR"
                if cell & 8 == 0:
                    extended_maze[i * 2 + 1][j * 2] = "CORRIDOR"
        return extended_maze

    def get_layout(
        self,
        screen: pygame.Surface,
        grid: List[List[str]],
        top_margin: int = 0,
    ) -> Tuple[int, int, int]:
        """Return ``(cell, offset_x, offset_y)`` for centring the maze.

        The math lives in ONE method everybody calls, so drawing and collision
        logic can never disagree about the geometry.

        Args:
            screen: The surface the maze is drawn on.
            grid: The expanded maze grid.
            top_margin: Pixels reserved at the top for the HUD (Task 8.3). The
                maze is laid out only in the space below this strip, so the HUD
                and the maze can never overlap.

        Returns:
            The square cell size and the letterbox offsets, in pixels.
        """
        rows = len(grid)
        cols = len(grid[0])
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        # Only the area below the reserved HUD strip is available for the maze.
        available_height = screen_height - top_margin

        # Square cells so the maze isn't stretched, centred with a letterbox.
        cell = min(screen_width // cols, available_height // rows)
        offset_x = (screen_width - cell * cols) // 2
        # Centre vertically WITHIN the available area, then push past the strip.
        offset_y = top_margin + (available_height - cell * rows) // 2
        return cell, offset_x, offset_y

    def draw(
        self,
        screen: pygame.Surface,
        grid: List[List[str]],
        top_margin: int = 0,
    ) -> None:
        """Draw the maze: solid fills, then carved channels for the tube look.

        The ``top_margin`` matches :meth:`get_layout` so the drawn walls line
        up with the shifted playfield.
        """
        rows = len(grid)
        cols = len(grid[0])
        cell, offset_x, offset_y = self.get_layout(screen, grid, top_margin)

        # Thickness of the blue "tube" outline. Thinner walls => wider corridors.
        border = max(2, cell // 4)

        screen.fill(self.BG_COLOR)

        def is_wall(r: int, c: int) -> bool:
            return 0 <= r < rows and 0 <= c < cols and grid[r][c] == "WALL"

        # Pass 1: fill every wall cell solid blue - and the "42" cells solid
        # magenta. FT_WALL is deliberately NOT hollowed out by pass 2, so the
        # 42 stays a bold filled shape that stands out from the outlined walls.
        for r in range(rows):
            for c in range(cols):
                x = offset_x + c * cell
                y = offset_y + r * cell
                if grid[r][c] == "FT_WALL":
                    pygame.draw.rect(screen, self.FT_COLOR, (x, y, cell, cell))
                elif grid[r][c] == "WALL":
                    pygame.draw.rect(screen, self.WALL_COLOR, (x, y, cell, cell))

        # Pass 2: carve a black channel through the middle of each wall cell,
        # extended toward any neighbouring wall so the channels join up. What's
        # left is a thin, continuous blue outline: the classic Pac-Man look.
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] != "WALL":
                    continue
                x = offset_x + c * cell
                y = offset_y + r * cell
                ix, iy = x + border, y + border
                iw = ih = cell - 2 * border
                if is_wall(r, c - 1):
                    ix -= border
                    iw += border
                if is_wall(r, c + 1):
                    iw += border
                if is_wall(r - 1, c):
                    iy -= border
                    ih += border
                if is_wall(r + 1, c):
                    ih += border
                if iw > 0 and ih > 0:
                    pygame.draw.rect(screen, self.BG_COLOR, (ix, iy, iw, ih))
