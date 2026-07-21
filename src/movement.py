"""Shared grid-movement helpers used by both the player and the ghosts.

Everything here is pure geometry over the expanded maze grid: converting pixel
positions to cell coordinates, checking grid alignment, testing whether a move
into a neighbouring cell is legal, and picking a step size that divides the
cell evenly. Keeping this in one module means the player and the ghosts can
never disagree about how the maze maps onto the screen.
"""
from typing import Dict, List, Tuple

# Unit step (dx, dy) in grid columns/rows for each named direction.
_DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "right": (1, 0),
    "left": (-1, 0),
    "up": (0, -1),
    "down": (0, 1),
}

# The reverse of each direction, used to forbid instant 180 turns.
_OPPOSITE: Dict[str, str] = {
    "right": "left",
    "left": "right",
    "up": "down",
    "down": "up",
}


def pixel_to_cell(
    x: int, y: int, cell: int, offset_x: int, offset_y: int
) -> Tuple[int, int]:
    """Return the ``(row, col)`` cell containing a sprite's centre.

    Args:
        x: Sprite's left pixel coordinate.
        y: Sprite's top pixel coordinate.
        cell: Cell size in pixels.
        offset_x: Left letterbox offset of the maze.
        offset_y: Top letterbox offset of the maze.

    Returns:
        The ``(row, col)`` grid coordinate of the sprite's centre.
    """
    row = (y + cell // 2 - offset_y) // cell
    col = (x + cell // 2 - offset_x) // cell
    return (row, col)


def is_aligned(x: int, y: int, cell: int, offset_x: int, offset_y: int) -> bool:
    """Return ``True`` when a pixel position sits exactly on a cell boundary.

    Alignment is the only moment a turn or a wall-stop may happen, which is
    what keeps sprites perfectly centred in the corridors.
    """
    return (x - offset_x) % cell == 0 and (y - offset_y) % cell == 0


def can_go(grid: List[List[str]], row: int, col: int, direction: str) -> bool:
    """Return ``True`` if the cell ``direction`` leads into is a corridor.

    Args:
        grid: The expanded maze grid of cell-type strings.
        row: Current row.
        col: Current column.
        direction: One of the keys in :data:`_DIRECTIONS`.

    Returns:
        ``True`` when the neighbouring cell exists and is a ``"CORRIDOR"``.
    """
    dx, dy = _DIRECTIONS[direction]
    r, c = row + dy, col + dx
    return (
        0 <= r < len(grid)
        and 0 <= c < len(grid[0])
        and grid[r][c] == "CORRIDOR"
    )


def pick_speed(cell: int) -> int:
    """Return the largest step size (<= ``cell // 6``) that divides ``cell``.

    The speed must divide the cell size evenly, otherwise a sprite would step
    over the exact alignment point between two cells and could never turn or be
    stopped by a wall again.
    """
    for candidate in range(max(1, cell // 6), 0, -1):
        if cell % candidate == 0:
            return candidate
    return 1
