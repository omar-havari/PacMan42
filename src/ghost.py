"""The ghosts: their chase/flee AI, frightened/eaten states, and rendering.

A :class:`GhostManager` owns all four ghosts so :class:`~src.GameDemo.GameDemo`
only ever talks to one object, exactly like :class:`~src.pacgums.PacgumManager`
owns every pac-gum.
"""
import os
from typing import List, Optional, Tuple

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

# NEW (Task 5.3): how long before flee ends the sprite starts flashing, and
# how fast it flashes. Lives here (not on GameDemo) since it's a ghost
# rendering detail, not a game-rule constant like the 7s flee duration.
_FLEE_WARNING_MS = 2000
_FLEE_FLASH_INTERVAL_MS = 200
_FLEE_COLOR = (33, 33, 255)            # classic frightened dark blue
_FLEE_WARNING_COLOR = (255, 255, 255)  # white flash before flee ends

# NEW (Task 5.4): how long an eaten ghost stays gone before it respawns.
_EATEN_DURATION_MS = 6000

# CHANGED (Task 8.6): the single knob controlling how fast ghosts move while
# fleeing. A frightened ghost only actually steps forward once every
# _FRIGHTENED_STEP_EVERY frames (2 = half speed), which is what makes it
# catchable. Previously this "2" was an inline literal in update(); pulling it
# out into one named constant makes the flee speed a single, obvious thing to
# tune - raise it to make fleeing ghosts slower/easier, lower it to make the
# chase harder.
_FRIGHTENED_STEP_EVERY = 2

# CHANGED (speed tuning): how many WHOLE base-speed steps a ghost takes per
# frame while chasing. Ghost speed is raised the same alignment-safe way as
# Pac-Man's - more whole steps per frame, never a bigger single step - so the
# base step still divides the cell exactly. Doubling this to 2 matches Pac-Man's
# doubled base speed, keeping the chase balance identical while everything moves
# faster. Frightened ghosts still move on only every _FRIGHTENED_STEP_EVERY-th
# step, so they stay proportionally slower (and catchable).
_GHOST_STEPS_PER_FRAME = 2

Cell = Tuple[int, int]
Color = Tuple[int, int, int]


class Ghost:
    """One ghost: distance-based chase/flee AI plus frightened/eaten states."""

    def __init__(
        self,
        screen: pygame.Surface,
        grid: List[List[str]],
        cell: int,
        offset_x: int,
        offset_y: int,
        color: Color,
        spawn_cell: Cell,
    ) -> None:
        """Spawn a ghost at ``spawn_cell`` in CHASE state, tinted ``color``."""
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.color = color
        self.spawn_cell = spawn_cell
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.speed = pick_speed(cell)

        # Frightened ghosts move slower so Pac-Man can catch them. `speed` is
        # already the smallest step that still divides the cell evenly, so it
        # can't just be halved; instead the ghost only steps forward on some
        # frames (see _FRIGHTENED_STEP_EVERY) - same step size, less often.
        self._frighten_tick = 0

        row, col = spawn_cell
        self.x = offset_x + col * cell
        self.y = offset_y + row * cell

        # Set BEFORE update() ever runs - update() reads self.direction, and
        # the ghost spawns already grid-aligned so update() enters its turn
        # logic on the very first frame.
        self.direction: Optional[str] = None
        self.state = "CHASE"
        self.eaten_until = 0    # 0 = not eaten; else a get_ticks() timestamp
        self.flashing = False

        ghost_file = 'Screenshot_From_2026-07-10_12-31-49-removebg-preview.png'
        ghost_image_path = os.path.join(_ASSETS, 'images', ghost_file)
        self.sprite: Optional[pygame.Surface]
        self.flee_sprite: Optional[pygame.Surface]
        self.flee_warning_sprite: Optional[pygame.Surface]
        try:
            raw = pygame.image.load(ghost_image_path).convert_alpha()
            raw = pygame.transform.scale(raw, (cell, cell))
            # Three tinted copies: normal colour, flee blue, flee-warning
            # white. Precomputed once here instead of re-tinting every frame.
            self.sprite = raw.copy()
            self.sprite.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            self.flee_sprite = raw.copy()
            self.flee_sprite.fill(_FLEE_COLOR, special_flags=pygame.BLEND_RGBA_MULT)
            self.flee_warning_sprite = raw.copy()
            self.flee_warning_sprite.fill(
                _FLEE_WARNING_COLOR, special_flags=pygame.BLEND_RGBA_MULT
            )
        except (FileNotFoundError, pygame.error):
            # Robustness: if the image is missing, draw a coloured square.
            print(f"Warning: ghost image '{ghost_file}' not found, using a plain block.")
            self.sprite = None
            self.flee_sprite = None
            self.flee_warning_sprite = None

    def current_cell(self) -> Cell:
        """Return the ``(row, col)`` cell the ghost's centre is in."""
        return pixel_to_cell(self.x, self.y, self.cell, self.offset_x, self.offset_y)

    def shift_time(self, delta: int) -> None:
        """Slide the respawn deadline forward by ``delta`` ms (pause support).

        The only absolute timestamp a ghost owns is its eaten/respawn deadline,
        so pushing that forward (when set) stops an eaten ghost secretly
        respawning while the game is frozen.
        """
        if self.eaten_until:
            self.eaten_until += delta

    def get_eaten(self) -> None:
        """Send this ghost home and hide it until its respawn timer elapses.

        Called when the player touches it while it is FRIGHTENED. It is sent
        straight back to its home corner and hidden until :meth:`update` lets
        it rejoin the chase.
        """
        row, col = self.spawn_cell
        self.x = self.offset_x + col * self.cell
        self.y = self.offset_y + row * self.cell
        self.direction = None
        self.state = "EATEN"
        self.eaten_until = pygame.time.get_ticks() + _EATEN_DURATION_MS

    def update(
        self,
        target_cell: Cell,
        frightened: bool = False,
        flashing: bool = False,
    ) -> None:
        """Advance the ghost one frame toward (or away from) ``target_cell``.

        Uses a distance-based direction choice at each intersection - the
        simplest correct approximation of the classic ghost AI. When
        ``frightened`` the same distance is used but the FARTHEST option is
        picked instead of the nearest.
        """
        # While eaten, sit hidden at the spawn corner until the timer elapses.
        if self.eaten_until:
            if pygame.time.get_ticks() < self.eaten_until:
                return
            self.eaten_until = 0
            # Force this respawn frame into CHASE even if the flee window that
            # got it eaten is still running (matching "respawns in CHASE"). If
            # that window is still active it goes back to FRIGHTENED next frame.
            frightened = False

        # CHANGED (speed tuning): take several WHOLE base-speed steps per frame.
        # Each _step() re-checks alignment and re-picks a direction, so the
        # cell-snapping and wall logic stay correct at any speed.
        for _ in range(_GHOST_STEPS_PER_FRAME):
            self._step(target_cell, frightened)

        self.state = "FRIGHTENED" if frightened else "CHASE"
        self.flashing = flashing

    def _step(self, target_cell: Cell, frightened: bool) -> None:
        """Advance the ghost one base-speed step toward/away from ``target_cell``.

        One movement sub-step: re-pick a direction when aligned on a cell, then
        move a single base-speed hop (or hold still this step when frightened
        and it isn't this ghost's turn to move).
        """
        if is_aligned(self.x, self.y, self.cell, self.offset_x, self.offset_y):
            row, col = self.current_cell()
            options = [d for d in _DIRECTIONS if can_go(self.grid, row, col, d)]
            # Don't immediately reverse unless it's the only way out - UNLESS
            # frightened: fleeing ghosts may double back to gain distance.
            if self.direction and len(options) > 1 and not frightened:
                options = [d for d in options if d != _OPPOSITE[self.direction]]
            if options:
                target_row, target_col = target_cell

                def distance_to_target(direction: str) -> int:
                    dx, dy = _DIRECTIONS[direction]
                    r, c = row + dy, col + dx
                    return (r - target_row) ** 2 + (c - target_col) ** 2

                if frightened:
                    self.direction = max(options, key=distance_to_target)
                else:
                    self.direction = min(options, key=distance_to_target)
            else:
                self.direction = None       # boxed in, shouldn't happen

        if self.direction:
            move_this_frame = True
            if frightened:
                self._frighten_tick += 1
                move_this_frame = self._frighten_tick % _FRIGHTENED_STEP_EVERY == 0
            else:
                self._frighten_tick = 0    # reset so flee always starts full

            if move_this_frame:
                dx, dy = _DIRECTIONS[self.direction]
                self.x += dx * self.speed
                self.y += dy * self.speed

    def draw(self) -> None:
        """Draw the ghost in its current state (hidden while EATEN)."""
        if self.state == "EATEN":
            return   # hidden until it respawns (Task 5.4)

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


class GhostManager:
    """Owns all four ghosts and fans one update/draw call out to each."""

    def __init__(
        self,
        screen: pygame.Surface,
        grid: List[List[str]],
        cell: int,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Build one ghost per maze corner, each a different colour."""
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        rows = len(grid)
        cols = len(grid[0])
        # Odd row/col indices are always corridors (walls sit on even edges),
        # so these corner cells are guaranteed walkable.
        corners: List[Cell] = [
            (1, 1),                # top-left
            (1, cols - 2),         # top-right
            (rows - 2, 1),         # bottom-left
            (rows - 2, cols - 2),  # bottom-right
        ]

        colors: List[Color] = [
            (255, 0, 0),      # red
            (255, 184, 255),  # pink
            (0, 255, 255),    # cyan
            (255, 184, 82),   # orange
        ]

        self.ghosts = [
            Ghost(screen, grid, cell, offset_x, offset_y, color, corner)
            for corner, color in zip(corners, colors)
        ]

    def update(self, target_cell: Cell, fright_remaining_ms: int = 0) -> None:
        """Update every ghost, sharing one flee timer so they stay in sync.

        Args:
            target_cell: Pac-Man's current cell (the chase/flee target).
            fright_remaining_ms: Milliseconds of flee time left; ``<= 0`` means
                the ghosts are not frightened at all.
        """
        frightened = fright_remaining_ms > 0
        flashing = 0 < fright_remaining_ms <= _FLEE_WARNING_MS
        for ghost in self.ghosts:
            ghost.update(target_cell, frightened, flashing)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw all four ghosts (each draws onto its own stored surface)."""
        for ghost in self.ghosts:
            ghost.draw()

    def shift_time(self, delta: int) -> None:
        """Fan the pause time-shift out to every ghost."""
        for ghost in self.ghosts:
            ghost.shift_time(delta)

    def resolve_player_contact(self, player_cell: Cell) -> int:
        """Eat any FRIGHTENED ghost sharing ``player_cell``.

        Returns:
            How many ghosts were eaten this frame, so the caller can award
            points without :class:`GhostManager` knowing anything about scoring.
        """
        eaten_count = 0
        for ghost in self.ghosts:
            if ghost.state == "FRIGHTENED" and ghost.current_cell() == player_cell:
                ghost.get_eaten()
                eaten_count += 1
        return eaten_count

    def resolve_chase_contact(self, player_cell: Cell) -> bool:
        """Return ``True`` if a dangerous CHASE-state ghost is on ``player_cell``.

        FRIGHTENED ghosts get eaten instead, and EATEN ghosts are hidden, so
        both are excluded here.
        """
        return any(
            ghost.state == "CHASE" and ghost.current_cell() == player_cell
            for ghost in self.ghosts
        )
