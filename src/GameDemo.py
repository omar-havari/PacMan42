import os
import random
import sys

import pygame

from src.Player import Player
from src.maze_loader import MazeLoader
from src.pacgums import PacgumManager
from src.ghost import GhostManager

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# Maze size in GENERATOR cells - the expanded WALL/CORRIDOR grid on screen
# is (2*w+1) x (2*h+1), so 15x15 becomes a 31x31 grid. Later the config's
# "level" array can override this per level.
MAZE_WIDTH = 15
MAZE_HEIGHT = 15
MAX_LEVEL = 10  # subject: the game is won after completing 10 levels

# NEW: brief "Ready" pause before each level's gameplay actually begins.
# Without this, ghosts (which move every frame regardless of input) got a
# free head start over a player who hasn't pressed a key yet.
_READY_COUNTDOWN_MS = 3000

# NEW (Task 6.1): when the level timer runs out, the game freezes on that
# exact frame for a beat before the next attempt's "Ready" countdown
# appears - see the "time_up_freeze_until" handling in update().
_TIME_UP_FREEZE_MS = 1000

# NEW (Task 5.5): same idea, but for a ghost catching Pac-Man - freeze on
# the exact frame of contact, then a "Ready" countdown, then back into the
# SAME level (grid + remaining pacgums untouched, only positions reset).
_GHOST_DEATH_FREEZE_MS = 1000


# CHANGED (Phase 4): GameDemo is no longer a thin wrapper around Player -
# it is now the real game screen. It owns the maze, the pacgums, the score
# and the level counter, and coordinates all of them each frame.
class GameDemo:
    def __init__(self, screen, config):
        self.screen = screen
        self.config = config  # Used to assign values to all the parameters needed
        self.maze = MazeLoader()

        # Score and level live HERE (not on the player) because they must
        # survive across levels while player/pacgums get rebuilt each level.
        self.score = 0
        self.level = 1
        self.victory_time = None

        # Placeholder for Phase 5: eating a super-pacgum starts this timer;
        # the ghosts will read it to know they are edible. Wiring it now
        # means Task 4.2 is complete and Phase 5 just has to consume it.
        self.fright_until = 0

        self.hud_font = self._load_font(
            os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 24
        )

        # If maze generation fails we don't crash - update() returns True
        # on the first frame and the menu loop takes the screen back.
        self.failed = not self._start_level()

    def _load_font(self, path, size):
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Error: font file '{path}' not found. Cannot start the game.")
            pygame.quit()
            sys.exit(1)

    # NEW (Task 4.3): builds one level - maze, player, pacgums, ghosts. Called
    # for level 1 from __init__ and again every time a level is cleared. This
    # is SETUP (runs once per level) - per-frame movement/drawing lives in
    # update()/draw(), not here. ALSO called again by update() itself when
    # Task 6.1's countdown timer runs out, to regenerate the SAME level
    # number - see the comment there for why.
    def _start_level(self):
        # Subject rule: level 1 uses the fixed seed from the config (so the
        # first maze is reproducible), every later level gets a random seed.
        # This still holds true even when level 1 is being regenerated after
        # a timeout, so it stays reproducible on retries too.
        if self.level == 1:
            seed = self.config.seed
        else:
            seed = random.randrange(1_000_000)

        # NEW (Task 6.2): config's "level" array can override the maze size
        # for a given level (1-indexed -> config.level[level - 1]). Any
        # level without a valid entry - including every level once the
        # array runs out, which happens immediately if it's the default
        # empty list - just falls back to the fixed MAZE_WIDTH/HEIGHT, i.e.
        # procedural generation exactly as before.
        width, height = MAZE_WIDTH, MAZE_HEIGHT
        idx = self.level - 1
        if 0 <= idx < len(self.config.level):
            entry = self.config.level[idx]
            if isinstance(entry, dict):
                candidate_width = entry.get("width")
                candidate_height = entry.get("height")
                if isinstance(candidate_width, int) and candidate_width > 0:
                    width = candidate_width
                if isinstance(candidate_height, int) and candidate_height > 0:
                    height = candidate_height

        self.grid = self.maze.generate(width, height, seed)
        if self.grid is None:
            # MazeLoader already printed the real error (Task 2.2).
            print("Error: could not generate the maze, returning to menu.")
            return False

        cell, offset_x, offset_y = self.maze.get_layout(self.screen, self.grid)

        # Lives carry over between levels: the very first call (no player
        # yet) pulls the starting count from the config, every later call -
        # whether advancing to a new level or regenerating this one after a
        # Task 6.1 timeout - carries over whatever the player currently has.
        if not hasattr(self, "player"):
            lives = self.config.lives
        else:
            lives = self.player.lives

        self.player = Player(self.screen, lives, self.grid, cell, offset_x, offset_y)
        self.pacgums = PacgumManager(
            self.grid, self.player.current_cell(), cell, offset_x, offset_y
        )
        # NEW (Task 5.1): 4 ghosts, one per maze corner. Rebuilt every level
        # like the player and pacgums.
        self.ghosts = GhostManager(self.screen, self.grid, cell, offset_x, offset_y)

        # NEW: "Ready" countdown (3, 2, 1) before gameplay begins - see
        # update()/draw(). Both the player and the ghosts stay frozen until
        # it ends, so ghosts never get a head start over an idle player.
        # The Task 6.1 level timer starts counting from the exact moment
        # THIS ends, not from level construction - so it truly starts
        # "regardless" of player input rather than depending on it.
        now = pygame.time.get_ticks()
        self.countdown_until = now + _READY_COUNTDOWN_MS
        self.level_start_time = self.countdown_until
        # Cleared here so a fresh level never starts mid-freeze from a
        # timeout or ghost death that happened on a previous attempt.
        self.time_up_freeze_until = None
        self.ghost_death_freeze_until = None
        return True

    # NEW (Task 5.5): a ghost caught Pac-Man. Unlike _start_level(), this
    # does NOT touch self.grid or self.pacgums - the maze and whichever
    # pacgums are still uneaten stay exactly as they were. Only positions
    # reset: Pac-Man back to the centre, ghosts back to their spawn
    # corners in CHASE - then the normal "Ready" countdown runs again
    # before movement resumes, same as any other level (re)start.
    def _restart_level_in_place(self):
        self.player.respawn()
        cell, offset_x, offset_y = self.maze.get_layout(self.screen, self.grid)
        self.ghosts = GhostManager(self.screen, self.grid, cell, offset_x, offset_y)
        self.fright_until = 0

        now = pygame.time.get_ticks()
        self.countdown_until = now + _READY_COUNTDOWN_MS
        self.level_start_time = self.countdown_until

    def handle_event(self, event):
        self.player.handle_event(event)

    def update(self):
        # Maze generation failed in __init__ -> leave immediately, cleanly.
        if self.failed:
            return True

        # --- has the 4-second victory screen finished showing? ---
        if self.victory_time:
            return pygame.time.get_ticks() - self.victory_time >= 4000

        # --- "Ready" countdown: nothing moves, nothing ticks, until it ends ---
        if pygame.time.get_ticks() < self.countdown_until:
            return False

        # --- Task 6.1: time's up, frozen beat before the next attempt ---
        # The moment the timer hit zero, everything froze exactly where it
        # was (see below) instead of instantly regenerating - this holds
        # that freeze for _TIME_UP_FREEZE_MS before restarting the same
        # level's "Ready" countdown.
        if self.time_up_freeze_until is not None:
            if pygame.time.get_ticks() < self.time_up_freeze_until:
                return False
            self.time_up_freeze_until = None
            if not self._start_level():
                return True
            return False

        # --- Task 5.5: ghost caught Pac-Man, frozen beat before retrying ---
        # Mirrors the timeout freeze above, but restarts IN PLACE
        # (_restart_level_in_place) instead of a full _start_level(), so
        # the maze and any pacgums already eaten stay exactly as they were.
        if self.ghost_death_freeze_until is not None:
            if pygame.time.get_ticks() < self.ghost_death_freeze_until:
                return False
            self.ghost_death_freeze_until = None
            self._restart_level_in_place()
            return False

        # --- Task 6.1: per-level countdown timer ---
        # DECISION (documented here per the subtask): running out of time
        # never costs a life or ends the run - it just regenerates the SAME
        # level with a fresh maze/pacgums/ghosts/timer, no matter how many
        # times it happens. Only ghost contact (Task 5.5) costs lives.
        # Checked BEFORE the player/ghosts move this frame, so the freeze
        # above genuinely holds the exact frame the timer expired - nobody
        # gets one extra step in before it kicks in.
        time_left_ms = (
            self.config.level_max_time * 1000
            - (pygame.time.get_ticks() - self.level_start_time)
        )
        if time_left_ms <= 0:
            self.time_up_freeze_until = pygame.time.get_ticks() + _TIME_UP_FREEZE_MS
            return False

        # Player moves first; if the game-over screen is up this returns
        # True once it has been shown long enough.
        if self.player.update():
            return True
        if self.player.game_over_time:
            return False  # game-over screen still showing, skip the rest

        # Ghost update - chase Pac-Man (Task 5.2), or flee while a
        # super-pacgum's effect is still active (Task 5.3).
        fright_remaining = self.fright_until - pygame.time.get_ticks()
        self.ghosts.update(self.player.current_cell(), fright_remaining)

        # --- Task 5.4: eating a frightened ghost ---
        eaten_ghosts = self.ghosts.resolve_player_contact(self.player.current_cell())
        self.score += eaten_ghosts * self.config.points_per_ghost

        # --- Task 5.5: real ghost contact - only CHASE-state ghosts are
        # dangerous, and the respawn invincibility window (Task 3.3) stops
        # a single hit from chaining into another death right as the
        # freeze below ends. Losing a life still ends the game at 0, same
        # as ever - it just no longer respawns instantly: it freezes on
        # this exact contact frame first (ghost_death_freeze_until,
        # handled above), then reruns the "Ready" countdown before
        # resuming, with the maze/remaining pacgums untouched.
        if not self.player.is_invincible() and self.ghosts.resolve_chase_contact(self.player.current_cell()):
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.player.game_over_time = pygame.time.get_ticks()
                return False  # game-over screen just triggered, skip the rest
            self.ghost_death_freeze_until = pygame.time.get_ticks() + _GHOST_DEATH_FREEZE_MS
            return False

        # --- Task 4.2: collection and scoring ---
        # Whatever cell pacman's centre is in, try to eat what's there.
        # Points only ever get ADDED, so the score can never decrease.
        eaten = self.pacgums.collect(self.player.current_cell())
        if eaten == "PACGUM":
            self.score += self.config.points_per_pacgum
        elif eaten == "SUPER":
            self.score += self.config.points_per_super_pacgum
            # Ghosts become edible for 7 seconds (consumed in Phase 5).
            self.fright_until = pygame.time.get_ticks() + 7000

        # --- Task 4.3: level win condition ---
        if self.pacgums.remaining() == 0:
            if self.level >= MAX_LEVEL:
                self.victory_time = pygame.time.get_ticks()
            else:
                self.level += 1
                # New maze, new pacgums - score and lives carry over.
                if not self._start_level():
                    return True

        return False

    def draw(self):
        if self.failed:
            return

        if self.victory_time:
            self._draw_center_text("You  Win!")
            return

        if self.player.game_over_time:
            self.player.draw()  # Player draws the Game Over screen itself
            return

        # NEW: "Ready" freeze - a plain black screen with a white countdown
        # number, same full-screen-takeover style as the Game Over/Victory
        # screens, instead of showing the maze underneath. The new level is
        # fully built already (see _start_level()) but stays hidden until
        # this ends.
        remaining_ms = self.countdown_until - pygame.time.get_ticks()
        if remaining_ms > 0:
            remaining_s = remaining_ms // 1000 + 1
            self._draw_center_text(str(remaining_s), color=(255, 255, 255))
            return

        # Draw order = layers: maze fills the background, pacgums sit in the
        # corridors, ghosts on top of those, pacman above the ghosts (so he
        # stays visible on overlap), HUD text above everything.
        self.maze.draw(self.screen, self.grid)
        self.pacgums.draw(self.screen)
        self.ghosts.draw(self.screen)
        self.player.draw()

        # Task 4.2/6.1: live score + time display (a proper HUD with full
        # layout comes in Phase 8).
        time_left = max(0, self.config.level_max_time - (pygame.time.get_ticks() - self.level_start_time) // 1000)
        hud = self.hud_font.render(
            f"Score {self.score}  Level {self.level}  Lives {self.player.lives}  Time {time_left}",
            False,
            (255, 255, 0),
        )
        self.screen.blit(hud, (10, 10))

    # NEW: victory screen, same style as the Game Over screen. Sized at 120
    # (not 300) so the longer text still fits on smaller screens. Also
    # reused for the white "Ready" countdown via the color param.
    def _draw_center_text(self, text, color=(255, 255, 0)):
        font = self._load_font(
            os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 120
        )
        rendered = font.render(text, False, color)
        box = rendered.get_rect(
            center=(self.screen.get_width() / 2, self.screen.get_height() / 2)
        )
        self.screen.fill((0, 0, 0))
        self.screen.blit(rendered, box)
