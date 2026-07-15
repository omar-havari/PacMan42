import os

import pygame

from src.movement import (
    _DIRECTIONS,
    _OPPOSITE,
    can_go,
    is_aligned,
    pick_speed,
    pixel_to_cell,
)

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

_STATES = ["CHASE", "SCATTER", "FRIGHTENED", "EATEN"]

# NEW (Task 5.3): how long before flee ends the sprite starts flashing, and
# how fast it flashes. Lives here (not on GameDemo) since it's a ghost
# rendering detail, not a game-rule constant like the 7s flee duration.
_FLEE_WARNING_MS = 2000
_FLEE_FLASH_INTERVAL_MS = 200
_FLEE_COLOR = (33, 33, 255)        # classic frightened dark blue
_FLEE_WARNING_COLOR = (255, 255, 255)  # white flash before flee ends


class Ghost:
    def __init__(self, screen, grid, cell, offset_x, offset_y, color, spawn_cell):
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.color = color
        self.spawn_cell = spawn_cell
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.speed = pick_speed(cell)

        row, col = spawn_cell
        self.x = offset_x + col * cell
        self.y = offset_y + row * cell

        # Set BEFORE update() ever runs - update() reads self.direction, and
        # the ghost spawns already grid-aligned so update() enters its turn
        # logic on the very first frame.
        self.direction = None
        self.state = "CHASE"   # 5.1 only uses CHASE; FLEE/EATEN come in 5.3/5.4

        ghost_file = 'Screenshot_From_2026-07-10_12-31-49-removebg-preview.png'
        ghost_image_path = os.path.join(_ASSETS, 'images', ghost_file)
        try:
            raw = pygame.image.load(ghost_image_path).convert_alpha()
            raw = pygame.transform.scale(raw, (cell, cell))
            # --- three tinted copies: normal color, flee blue, flee-warning
            # white. Precomputed once here instead of re-tinting every frame.
            self.sprite = raw.copy()
            self.sprite.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            self.flee_sprite = raw.copy()
            self.flee_sprite.fill(_FLEE_COLOR, special_flags=pygame.BLEND_RGBA_MULT)
            self.flee_warning_sprite = raw.copy()
            self.flee_warning_sprite.fill(_FLEE_WARNING_COLOR, special_flags=pygame.BLEND_RGBA_MULT)
        except (FileNotFoundError, pygame.error):
            # robustness: if the image is missing, don't crash - draw a colored square
            print(f"Warning: ghost image '{ghost_file}' not found, using a plain block.")
            self.sprite = None
            self.flee_sprite = None
            self.flee_warning_sprite = None

    def current_cell(self):
        return pixel_to_cell(self.x, self.y, self.cell, self.offset_x, self.offset_y)

    # NEW (Task 5.2/5.3): chase/flee behaviour. Distance-based direction
    # choice at each intersection - simplest correct approximation of the
    # classic ghost AI, no need for a full pathfinding search over the maze
    # graph. When frightened, the exact same distance calculation is used
    # but the ghost picks the FARTHEST option instead of the nearest one.
    def update(self, target_cell, frightened=False, flashing=False):
        if is_aligned(self.x, self.y, self.cell, self.offset_x, self.offset_y):
            row, col = self.current_cell()
            options = [d for d in _DIRECTIONS if can_go(self.grid, row, col, d)]
            # don't immediately reverse unless it's the only way out (dead
            # end) - UNLESS frightened: fleeing ghosts are allowed to double
            # back on themselves to put distance between them and Pac-Man.
            if self.direction and len(options) > 1 and not frightened:
                options = [d for d in options if d != _OPPOSITE[self.direction]]
            if options:
                target_row, target_col = target_cell

                # squared distance from the cell a direction leads into to
                # Pac-Man's cell - no need for a real sqrt, it doesn't
                # change which option is smallest/largest.
                def distance_to_target(direction):
                    dx, dy = _DIRECTIONS[direction]
                    r, c = row + dy, col + dx
                    return (r - target_row) ** 2 + (c - target_col) ** 2

                if frightened:
                    self.direction = max(options, key=distance_to_target)
                else:
                    self.direction = min(options, key=distance_to_target)
            else:
                self.direction = None       # boxed in, shouldn't happen on a real maze

        if self.direction:
            dx, dy = _DIRECTIONS[self.direction]
            self.x += dx * self.speed
            self.y += dy * self.speed

        self.state = "FRIGHTENED" if frightened else "CHASE"
        self.flashing = flashing

    def draw(self):
        sprite = self.sprite
        if self.state == "FRIGHTENED":
            flash_on = (pygame.time.get_ticks() // _FLEE_FLASH_INTERVAL_MS) % 2 == 0
            if self.flashing and flash_on:
                sprite = self.flee_warning_sprite
            else:
                sprite = self.flee_sprite

        if sprite:
            self.screen.blit(sprite, (self.x, self.y))
        else:
            color = _FLEE_COLOR if self.state == "FRIGHTENED" else self.color
            pygame.draw.rect(
                self.screen,
                color,
                (self.x, self.y, self.cell, self.cell),
            )


# Owns all 4 ghosts so GameDemo only ever talks to one object, exactly like
# PacgumManager owns every pacgum. One update()/draw() call fans out to all
# four ghosts.
class GhostManager:
    def __init__(self, screen, grid, cell, offset_x, offset_y):
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        rows = len(grid)
        cols = len(grid[0])
        # The 4 maze corners. Odd row/col indices are always corridors (the
        # wall border sits on the even edges), so these are guaranteed
        # walkable - same trick PacgumManager uses for super-pacgums.
        corners = [
            (1, 1),               # top-left
            (1, cols - 2),        # top-right
            (rows - 2, 1),        # bottom-left
            (rows - 2, cols - 2), # bottom-right
        ]

        colors = [
            (255, 0, 0),      # red
            (255, 184, 255),  # pink
            (0, 255, 255),    # cyan
            (255, 184, 82),   # orange
        ]

        # zip pairs each corner with one color: corner 1 -> red, etc.
        self.ghosts = [
            Ghost(screen, grid, cell, offset_x, offset_y, color, corner)
            for corner, color in zip(corners, colors)
        ]

    # NEW (Task 5.3): fright_remaining_ms is how much flee time is left
    # (0 or less = not frightened at all). Computed once here so every
    # ghost stays perfectly in sync instead of each one tracking its own
    # timer.
    def update(self, target_cell, fright_remaining_ms=0):
        frightened = fright_remaining_ms > 0
        flashing = 0 < fright_remaining_ms <= _FLEE_WARNING_MS
        for ghost in self.ghosts:
            ghost.update(target_cell, frightened, flashing)

    def draw(self, screen):
        for ghost in self.ghosts:
            ghost.draw()
