_DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "up": (0, -1),
    "down": (0, 1),
}

_OPPOSITE = {"right": "left", "left": "right", "up": "down", "down": "up"}


def pixel_to_cell(x, y, cell, offset_x, offset_y):
    row = (y + cell // 2 - offset_y) // cell
    col = (x + cell // 2 - offset_x) // cell
    return (row, col)


def is_aligned(x, y, cell, offset_x, offset_y):
    return (x - offset_x) % cell == 0 and (y - offset_y) % cell == 0


def can_go(grid, row, col, direction):
    dx, dy = _DIRECTIONS[direction]
    r, c = row + dy, col + dx
    return (
        0 <= r < len(grid)
        and 0 <= c < len(grid[0])
        and grid[r][c] == "CORRIDOR"
    )


def pick_speed(cell):
    for candidate in range(max(1, cell // 6), 0, -1):
        if cell % candidate == 0:
            return candidate
    return 1