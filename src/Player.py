import sys
import pygame
import os

from src.movement import _DIRECTIONS, _OPPOSITE

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# NEW (Task 3.3/5.5): short grace period after respawning where ghost
# contact can't cost another life - without it, respawning back into a
# ghost's current cell (or one it reaches a frame later) could chain into
# an instant second death.
_INVINCIBILITY_MS = 1000


class Player:
    # CHANGED (Phase 4 prerequisite = Tasks 3.2/3.3): the player now lives
    # INSIDE the maze. It receives the grid plus the layout numbers
    # (cell size and letterbox offsets) from MazeLoader.get_layout(), so
    # its pixel position always lines up with the walls drawn on screen.
    def __init__(self, screen, lives, grid, cell, offset_x, offset_y):

        self.screen = screen
        self.grid = grid
        self.cell = cell
        self.offset_x = offset_x
        self.offset_y = offset_y

        self.current_frame = 0
        self.last_switch = pygame.time.get_ticks()
        self.lives = lives  # Number of lives
        self.game_over_time = None

        # Movement is CELL-SNAPPED: pacman travels from cell centre to cell
        # centre. "direction" is where he is going right now,
        # "wanted_direction" is the last arrow key pressed. The wanted turn
        # is applied the moment he is aligned with the grid AND the target
        # cell is a corridor - exactly like the arcade game, where you can
        # press "up" early and pacman turns at the next junction.
        self.direction = None
        self.wanted_direction = None

        # The speed must divide the cell size evenly. If it didn't, pacman
        # would step OVER the exact alignment point between two cells and
        # the "am I aligned?" check below would never be true again, so he
        # could never turn or be stopped by a wall.
        self.speed = 1
        for candidate in range(max(1, cell // 6), 0, -1):
            if cell % candidate == 0:
                self.speed = candidate
                break

        # *************ANIMATION SET-UP *****************
        # Load pacman images: open, half-open, closed
        figure_paths = [
            os.path.join(_ASSETS, 'images', 'Screenshot_From_2026-07-10_12-31-14-removebg-preview.png'),
            os.path.join(_ASSETS, 'images', 'Screenshot_From_2026-07-10_12-31-23-removebg-preview.png'),
            os.path.join(_ASSETS, 'images', 'Screenshot_From_2026-07-10_12-31-34-removebg-preview.png'),
        ]

        self.frames = [
            pygame.image.load(figure_paths[0]).convert_alpha(),
            pygame.image.load(figure_paths[1]).convert_alpha(),
            pygame.image.load(figure_paths[2]).convert_alpha(),
        ]
        # CHANGED: frames are scaled to the maze cell size instead of a
        # fixed 150x150, so pacman fits inside a corridor at any resolution.
        self.frames = [
            pygame.transform.scale(frame, (self.cell, self.cell))
            for frame in self.frames
        ]

        self.respawn()

    # NEW (Task 3.3): spawn/respawn in the middle of the maze. The expanded
    # grid always has odd dimensions and every odd row/column index is a
    # corridor, so the exact centre cell is guaranteed to be walkable.
    def respawn(self):
        row = len(self.grid) // 2
        col = len(self.grid[0]) // 2
        self.x = self.offset_x + col * self.cell
        self.y = self.offset_y + row * self.cell
        self.direction = None
        self.wanted_direction = None
        self.rotated = self.frames[self.current_frame]
        # NEW (Task 3.3/5.5): brief invincibility so respawning doesn't
        # immediately chain into another ghost-contact death.
        self.invincible_until = pygame.time.get_ticks() + _INVINCIBILITY_MS

    # NEW (Task 5.5): used by GameDemo before charging a ghost-contact life
    # loss, so the respawn grace period above actually does something.
    def is_invincible(self):
        return pygame.time.get_ticks() < self.invincible_until

    # NEW: pixel position -> grid cell. Uses the CENTRE of the sprite so
    # the answer doesn't flip early while pacman is between two cells.
    # GameDemo also calls this every frame to know which pacgum to eat.
    def current_cell(self):
        row = (self.y + self.cell // 2 - self.offset_y) // self.cell
        col = (self.x + self.cell // 2 - self.offset_x) // self.cell
        return (row, col)

    # NEW (Task 3.2): "can pacman leave his current cell in that direction?"
    # This is the whole wall-collision system - movement only ever starts
    # toward a neighbouring CORRIDOR cell, so walls are simply never entered.
    def _can_go(self, direction):
        dx, dy = _DIRECTIONS[direction]
        row, col = self.current_cell()
        r, c = row + dy, col + dx
        return (
            0 <= r < len(self.grid)
            and 0 <= c < len(self.grid[0])
            and self.grid[r][c] == "CORRIDOR"
        )

    # NEW: small helper so we don't repeat the same try/except every time
    # we need to load a font. Added "self" since it's a method now.
    def load_path(self, path, size):
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Error: font file '{path}' not found. Cannot start the game.")
            pygame.quit()
            sys.exit(1)

    # CHANGED: arrow keys no longer change direction instantly - they only
    # record the WISH. update() decides when the turn actually happens
    # (next time pacman is aligned with the grid and the way is free).
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.wanted_direction = "left"
            elif event.key == pygame.K_RIGHT:
                self.wanted_direction = "right"
            elif event.key == pygame.K_UP:
                self.wanted_direction = "up"
            elif event.key == pygame.K_DOWN:
                self.wanted_direction = "down"

    def update(self):
        # --- has the 4-second game-over screen finished showing? ---
        # While the game-over screen is up, nothing else should move.
        if self.game_over_time:
            return pygame.time.get_ticks() - self.game_over_time >= 4000

        # A 180° turn is always allowed, even in the middle of a corridor -
        # the cell behind pacman is the one he just came from, so it must
        # be free. Every OTHER turn has to wait for grid alignment below.
        if (
            self.direction
            and self.wanted_direction == _OPPOSITE[self.direction]
        ):
            self.direction = self.wanted_direction

        # "Aligned" = pixel position sits exactly on a cell boundary. This
        # is the only moment a turn or a wall-stop can happen, which is what
        # keeps pacman perfectly centred in the corridors.
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

            # --- animation timer: switch mouth frame every 150ms ---
            # Only animated while moving, so a stopped pacman doesn't chew air.
            now = pygame.time.get_ticks()
            if now - self.last_switch >= 150:
                self.current_frame = (self.current_frame + 1) % 3
                self.last_switch = now

            # --- pick the correct rotated frame for the direction ---
            if self.direction == "right":
                self.rotated = self.frames[self.current_frame]
            elif self.direction == "left":
                self.rotated = pygame.transform.flip(self.frames[self.current_frame], True, False)
            elif self.direction == "up":
                self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 90)
            elif self.direction == "down":
                self.rotated = pygame.transform.rotate(self.frames[self.current_frame], 270)

        # NOTE: the old "out of screen bounds -> lose_life" checks are gone.
        # The maze border is a solid ring of WALL cells, so leaving the
        # screen is impossible now. Lives are lost to ghosts (Phase 5).

        return False      # still playing

    # CHANGED: draw() no longer fills the screen black - the maze is drawn
    # first by GameDemo and fills the background itself. Pacman only blits
    # his own sprite on top.
    def draw(self):
        screen_width, screen_height = self.screen.get_size()

        if self.game_over_time:
            game_over_font = self.load_path(os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 300)
            game_over = game_over_font.render(
                "Game Over",
                False,
                (255, 255, 0)
            )
            game_over_box = game_over.get_rect(
                center=(screen_width / 2, screen_height / 2)
            )
            self.screen.fill((0, 0, 0))
            self.screen.blit(game_over, game_over_box)
        else:
            self.screen.blit(self.rotated, (self.x, self.y))
