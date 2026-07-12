import os
import pygame

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')


# NEW (Tasks 4.1 + 4.2): owns every pacgum in the level - where they are,
# what kind they are, drawing them, and handing them to the player when he
# walks over one. GameDemo only has to ask "what did he just eat?" and
# "how many are left?".
class PacgumManager:
    DOT_COLOR = (255, 183, 174)  # the classic pale-pink arcade dot

    def __init__(self, grid, start_cell, cell, offset_x, offset_y):
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        # One dict holds everything: (row, col) -> "PACGUM" or "SUPER".
        # A dict (instead o
        # f writing into the grid) means eating one is a
        # single .pop() and counting the rest is a single len() - and the
        # maze grid stays purely about walls.
        self.pacgums = {}
        rows = len(grid)
        cols = len(grid[0])

        # Task 4.1: a small pacgum in EVERY corridor cell except the
        # player's starting cell (he shouldn't eat one while standing still).
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == "CORRIDOR" and (r, c) != start_cell:
                    self.pacgums[(r, c)] = "PACGUM"

        # Task 4.1: one super-pacgum in each of the 4 corners. The expanded
        # grid puts corridors on every odd row/column index, so the corner
        # corridor cells (1,1), (1,cols-2), (rows-2,1), (rows-2,cols-2)
        # are guaranteed to exist - no searching needed.
        corners = [
            (1, 1),
            (1, cols - 2),
            (rows - 2, 1),
            (rows - 2, cols - 2),
        ]
        for corner in corners:
            if corner in self.pacgums:
                self.pacgums[corner] = "SUPER"

        # Total at level start, kept for the win-condition check and later
        # for the HUD ("x / total eaten").
        self.total = len(self.pacgums)

        # The sprites. If an image is missing we don't crash (robustness
        # requirement) - draw() falls back to plain circles instead.
        # Normal pacgum = a single cigarette, super-pacgum = the full pack.
        # The cigarette is drawn smaller than the cell (about 2/3) so the
        # corridors don't look completely stuffed; the pack fills the cell.
        self.dot_size = max(4, cell * 2 // 3)
        self.dot_image = self._load_sprite(
            'ChatGPT Image Jul 11, 2026, 03_31_12 PM.png',
            (self.dot_size, self.dot_size)
        )
        self.super_image = self._load_sprite(
            'Screenshot_From_2026-07-10_12-32-10-removebg-preview.png',
            (cell, cell)
        )

    def _load_sprite(self, filename, size):
        try:
            image_path = os.path.join(_ASSETS, 'images', filename)
            image = pygame.image.load(image_path).convert_alpha()
            return pygame.transform.scale(image, size)
        except (FileNotFoundError, pygame.error):
            print(f"Warning: image '{filename}' not found, using a plain circle.")
            return None

    def remaining(self):
        return len(self.pacgums)

    # Task 4.2: called every frame with the player's current cell.
    # Returns "PACGUM", "SUPER", or None - and removes the eaten one in the
    # same step (dict.pop with a default never raises).
    def collect(self, cell_pos):
        return self.pacgums.pop(cell_pos, None)

    def draw(self, screen):
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
