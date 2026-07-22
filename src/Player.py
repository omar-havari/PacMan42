"""Pac-Man himself: cell-snapped movement, animation, lives and respawns.

The player lives INSIDE the maze - it receives the grid plus the layout numbers
(cell size and letterbox offsets) so its pixel position always lines up with
the walls drawn on screen.
"""
import os
import sys
from typing import List, Optional, Tuple

import pygame

from src.movement import _DIRECTIONS, _OPPOSITE

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# NEW (Task 3.3/5.5): short grace period after respawning where ghost contact
# can't cost another life - without it, respawning back into a ghost's cell
# could chain into an instant second death.
_INVINCIBILITY_MS = 1000

# CHANGED (speed tuning): how many WHOLE base-speed steps Pac-Man takes per
# frame. Speed is raised by taking more whole steps (not a bigger single step)
# so the cell-alignment invariant is never broken - see steps_per_frame below.
#   _BASE_STEPS_PER_FRAME  - normal play (was an implicit 1; doubled to 2).
#   _BOOST_STEPS_PER_FRAME - the `B` speed-boost cheat (kept at 2x the base).
_BASE_STEPS_PER_FRAME = 2
_BOOST_STEPS_PER_FRAME = 4

# The "Game Over" screen text colour - the project's theme blue (matches
# _TEXT_COLOR in screens.py), replacing the old yellow.
_GAME_OVER_COLOR = (90, 140, 255)


class Player:
    """The player sprite: movement, animation, lives and the game-over screen."""

    def __init__(
        self,
        screen: pygame.Surface,
        lives: int,
        grid: List[List[str]],
        cell: int,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Build the player inside the maze and spawn it at the centre."""
        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.current_frame = 0
        self.last_switch = pygame.time.get_ticks()
        self.lives = lives
        self.game_over_time: Optional[int] = None

        # Movement is CELL-SNAPPED: Pac-Man travels from cell centre to cell
        # centre. "direction" is where he is going now, "wanted_direction" is
        # the last arrow pressed, applied the moment he is aligned AND the
        # target cell is a corridor - exactly like the arcade game.
        self.direction: Optional[str] = None
        self.wanted_direction: Optional[str] = None

        # The speed must divide the cell size evenly, or Pac-Man would step
        # OVER the exact alignment point between two cells and could never turn
        # or be stopped by a wall again.
        self.speed = 1
        for candidate in range(max(1, cell // 6), 0, -1):
            if cell % candidate == 0:
                self.speed = candidate
                break

        # NEW (Task 9.1 - speed-boost cheat), CHANGED (speed tuning): how many
        # base-speed steps to take per frame. _BASE_STEPS_PER_FRAME = normal,
        # _BOOST_STEPS_PER_FRAME = the speed-boost cheat. Boosting by taking
        # extra WHOLE base-speed steps (instead of a bigger single step) keeps
        # the alignment invariant intact: the base speed is guaranteed to divide
        # the cell size, so every sub-step still lands exactly on the grid.
        self.steps_per_frame = _BASE_STEPS_PER_FRAME

        # --- animation set-up: open, half-open, closed mouth frames ---
        figure_paths = [
            os.path.join(
                _ASSETS, 'images',
                'Screenshot_From_2026-07-10_12-31-14-removebg-preview.png'
            ),
            os.path.join(
                _ASSETS, 'images',
                'Screenshot_From_2026-07-10_12-31-23-removebg-preview.png'
            ),
            os.path.join(
                _ASSETS, 'images',
                'Screenshot_From_2026-07-10_12-31-34-removebg-preview.png'
            ),
        ]

        # Task 10.4: a missing sprite must not crash the game. If any frame
        # fails to load, fall back to a plain yellow circle (same graceful
        # degradation the pac-gums and ghosts already use). Scale to the maze
        # cell size (not a fixed 150x150) so Pac-Man fits a corridor at any
        # resolution.
        self.frames: List[pygame.Surface] = self._load_frames(figure_paths)

        self.respawn()

    def _load_frames(self, figure_paths: List[str]) -> List[pygame.Surface]:
        """Load and scale the three mouth frames, or a circle fallback."""
        try:
            raw_frames = [
                pygame.image.load(p).convert_alpha() for p in figure_paths
            ]
            return [
                pygame.transform.scale(frame, (self.cell, self.cell))
                for frame in raw_frames
            ]
        except (FileNotFoundError, pygame.error):
            print("Warning: Pac-Man images not found, using a plain circle.")
            fallback = pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)
            pygame.draw.circle(
                fallback, (255, 255, 0),
                (self.cell // 2, self.cell // 2), self.cell // 2
            )
            return [fallback, fallback, fallback]

    def respawn(self) -> None:
        """Place Pac-Man at the maze centre with a brief invincibility window.

        The expanded grid always has odd dimensions and every odd row/column
        index is a corridor, so the exact centre cell is guaranteed walkable.
        """
        row = len(self.grid) // 2
        col = len(self.grid[0]) // 2
        self.x = self.offset_x + col * self.cell
        self.y = self.offset_y + row * self.cell
        self.direction = None
        self.wanted_direction = None
        self.rotated = self.frames[self.current_frame]
        # Brief invincibility so respawning doesn't chain into another death.
        self.invincible_until = pygame.time.get_ticks() + _INVINCIBILITY_MS

    def is_invincible(self) -> bool:
        """Return ``True`` during the post-respawn grace period."""
        return pygame.time.get_ticks() < self.invincible_until

    def set_speed_boost(self, on: bool) -> None:
        """Turn the speed-boost cheat on or off (extra base-speed steps/frame).

        On boosts to ``_BOOST_STEPS_PER_FRAME``; off restores the normal
        ``_BASE_STEPS_PER_FRAME``. Boosting via extra whole steps (rather than a
        bigger single step) means alignment is never broken - see
        ``steps_per_frame`` in ``__init__``.
        """
        self.steps_per_frame = _BOOST_STEPS_PER_FRAME if on else _BASE_STEPS_PER_FRAME

    def shift_time(self, delta: int) -> None:
        """Slide every absolute timer forward by ``delta`` ms (pause support).

        The invincibility window, the animation timer, and the game-over screen
        all resume exactly where they left off, as if no time passed.
        """
        self.invincible_until += delta
        self.last_switch += delta
        if self.game_over_time:
            self.game_over_time += delta

    def current_cell(self) -> Tuple[int, int]:
        """Return the ``(row, col)`` cell Pac-Man's centre is in."""
        row = (self.y + self.cell // 2 - self.offset_y) // self.cell
        col = (self.x + self.cell // 2 - self.offset_x) // self.cell
        return (row, col)

    def _can_go(self, direction: str) -> bool:
        """Return ``True`` if the neighbouring cell in ``direction`` is a corridor.

        This is the whole wall-collision system - movement only ever starts
        toward a neighbouring corridor cell, so walls are simply never entered.
        """
        dx, dy = _DIRECTIONS[direction]
        row, col = self.current_cell()
        r, c = row + dy, col + dx
        return (
            0 <= r < len(self.grid)
            and 0 <= c < len(self.grid[0])
            and self.grid[r][c] == "CORRIDOR"
        )

    def load_path(self, path: str, size: int) -> pygame.font.Font:
        """Load a font, exiting cleanly (no traceback) if the file is missing."""
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Error: font file '{path}' not found. Cannot start the game.")
            pygame.quit()
            sys.exit(1)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Record the last arrow key pressed as the WISHED direction.

        The turn itself happens later in :meth:`update`, the next time Pac-Man
        is aligned with the grid and the way is free.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.wanted_direction = "left"
            elif event.key == pygame.K_RIGHT:
                self.wanted_direction = "right"
            elif event.key == pygame.K_UP:
                self.wanted_direction = "up"
            elif event.key == pygame.K_DOWN:
                self.wanted_direction = "down"

    def update(self) -> bool:
        """Advance Pac-Man one frame; return ``True`` when the game should end.

        Takes ``steps_per_frame`` base-speed steps (normally 1; the speed-boost
        cheat makes it 2). Each step is a full base-speed move that divides the
        cell, so boosting never skips a grid-alignment point.
        """
        # While the game-over screen is up, nothing else should move.
        if self.game_over_time:
            return pygame.time.get_ticks() - self.game_over_time >= 4000

        for _ in range(self.steps_per_frame):
            self._step()

        # The maze border is a solid ring of WALL cells, so leaving the screen
        # is impossible; lives are lost to ghosts (Phase 5), not to bounds.
        return False

    def _step(self) -> None:
        """Perform one base-speed movement step (turn logic + move + animate)."""
        # A 180 turn is always allowed, even mid-corridor - the cell behind is
        # the one just left, so it must be free. Other turns wait for alignment.
        if (
            self.direction
            and self.wanted_direction == _OPPOSITE[self.direction]
        ):
            self.direction = self.wanted_direction

        # "Aligned" = pixel position sits exactly on a cell boundary. The only
        # moment a turn or wall-stop can happen, keeping Pac-Man centred.
        aligned = (
            (self.x - self.offset_x) % self.cell == 0
            and (self.y - self.offset_y) % self.cell == 0
        )
        if aligned:
            if self.wanted_direction and self._can_go(self.wanted_direction):
                self.direction = self.wanted_direction
            if self.direction and not self._can_go(self.direction):
                self.direction = None  # wall ahead: stop and wait

        if self.direction:
            dx, dy = _DIRECTIONS[self.direction]
            self.x += dx * self.speed
            self.y += dy * self.speed

            # Animation timer: switch mouth frame every 150ms, only while moving.
            now = pygame.time.get_ticks()
            if now - self.last_switch >= 150:
                self.current_frame = (self.current_frame + 1) % 3
                self.last_switch = now

            # Pick the correct rotated frame for the direction.
            frame = self.frames[self.current_frame]
            if self.direction == "right":
                self.rotated = frame
            elif self.direction == "left":
                self.rotated = pygame.transform.flip(frame, True, False)
            elif self.direction == "up":
                self.rotated = pygame.transform.rotate(frame, 90)
            elif self.direction == "down":
                self.rotated = pygame.transform.rotate(frame, 270)

    def draw(self) -> None:
        """Blit Pac-Man's sprite, or the full-screen Game Over text if dead."""
        screen_width, screen_height = self.screen.get_size()

        if self.game_over_time:
            text = "Game Over"
            font_path = os.path.join(
                _ASSETS, 'fonts', 'PressStart2P-Regular.ttf'
            )
            # Size the text to the screen: render once at a reference size,
            # then scale that size so the text fills ~85% of the width without
            # exceeding half the height. A fixed 300px font overflowed the
            # window; this fits every resolution.
            ref_size = 100
            ref_w, ref_h = self.load_path(font_path, ref_size).size(text)
            scale = min(
                screen_width * 0.85 / ref_w,
                screen_height * 0.5 / ref_h,
            )
            size = max(8, int(ref_size * scale))
            game_over_font = self.load_path(font_path, size)
            game_over = game_over_font.render(text, False, _GAME_OVER_COLOR)
            game_over_box = game_over.get_rect(
                center=(screen_width / 2, screen_height / 2)
            )
            self.screen.fill((0, 0, 0))
            self.screen.blit(game_over, game_over_box)
        else:
            self.screen.blit(self.rotated, (self.x, self.y))
