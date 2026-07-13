from src.movement import _DIRECTIONS, pick_speed

_STATES = ["CHASE", "SCATTER", "FRIGHTENED","EATEN"]


class Ghost:
    def __init__(self, screen, grid, cell, offset_x, offset_y, color, spawn_cell):
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.color = color
        self.spawn_cell = spawn_cell

        self.speed = pick_speed(cell)

        row,col = spawn_cell
        self.offset_x = offset_x +col *cell
        self.offset_y = offset_y +row *cell


    def update(self):
        dx, dy = _DIRECTIONS[self.direction]
        self.x += dx * self.speed
        self.y += dy * self.speed

        