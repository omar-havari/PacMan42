import os
import random

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
            image = pygame.image.load(ghost_image_path).convert_alpha()
            image = pygame.transform.scale(image, (cell, cell))
            # --- tint it to this ghost's color ---
            image.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            self.sprite = image
        except (FileNotFoundError, pygame.error):
            # robustness: if the image is missing, don't crash - draw a colored square
            print(f"Warning: ghost image '{ghost_file}' not found, using a plain block.")
            self.sprite = None

    def current_cell(self):
        return pixel_to_cell(self.x, self.y, self.cell, self.offset_x, self.offset_y)

    def update(self):
        if is_aligned(self.x, self.y, self.cell, self.offset_x, self.offset_y):
            row, col = self.current_cell()
            options = [d for d in _DIRECTIONS if can_go(self.grid, row, col, d)]
            # don't immediately reverse unless it's the only way out (dead end)
            if self.direction and len(options) > 1:
                options = [d for d in options if d != _OPPOSITE[self.direction]]
            if options:
                self.direction = random.choice(options)
            else:
                self.direction = None       # boxed in, shouldn't happen on a real maze

        if self.direction:
            dx, dy = _DIRECTIONS[self.direction]
            self.x += dx * self.speed
            self.y += dy * self.speed

    def draw(self):
        if self.sprite:
            self.screen.blit(self.sprite, (self.x, self.y))
        else:
            pygame.draw.rect(
                self.screen,
                self.color,
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

    def update(self):
        for ghost in self.ghosts:
            ghost.update()

    def draw(self, screen):
        for ghost in self.ghosts:
            ghost.draw()
