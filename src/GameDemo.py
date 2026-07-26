"""The in-game screen: the maze, player, pac-gums, ghosts, HUD and cheats.

:class:`GameDemo` is the real gameplay screen. It owns the maze, the pac-gums,
the score and level counters, the four ghosts, and coordinates all of them each
frame. It exposes the small ``handle_event``/``update``/``draw`` contract the
main loop in :mod:`src.app` drives, plus pause support (Task 8.4) and the cheat
toggles (Phase 9).
"""
import os
import sys
from typing import List, Optional, Tuple

import pygame

from src.config import Config
from src.Player import Player
from src.maze_loader import MazeLoader
from src.pacgums import PacgumManager
from src.ghost import GhostManager

from src.resources import asset_dir
_ASSETS = asset_dir()

# Maze size in GENERATOR cells - the expanded WALL/CORRIDOR grid on screen is
# (2*w+1) x (2*h+1), so 15x15 becomes a 31x31 grid.
MAZE_WIDTH = 15
MAZE_HEIGHT = 15
MAX_LEVEL = 10  # subject: the game is won after completing 10 levels

# Brief "Ready" pause before each level begins, so ghosts (which move every
# frame regardless of input) don't get a head start over an idle player.
_READY_COUNTDOWN_MS = 3000

# Task 6.1: when the level timer runs out, freeze on that exact frame for a
# beat before the next attempt's "Ready" countdown.
_TIME_UP_FREEZE_MS = 1000

# Task 5.5: same idea, but for a ghost catching Pac-Man - freeze on the exact
# frame of contact, then a countdown, then back into the SAME level.
_GHOST_DEATH_FREEZE_MS = 1000

# Task 8.3: height in pixels of the HUD bar reserved at the top of the screen.
# The maze layout keeps this strip clear so the score/lives/level/time line
# can never overlap the maze below.
_HUD_HEIGHT = 60

# Phase 9 / Task 9.1: the cheat keys. Kept in one place so the handling below
# and the Instructions screen document the exact same keys. Chosen to never
# collide with the arrow keys (movement) or P/ESC (pause).
#   I - toggle invincibility   G - toggle ghost freeze   B - toggle speed boost
#   L - grant one extra life    N - skip to the next level
_CHEAT_INVINCIBLE = pygame.K_i
_CHEAT_GHOST_FREEZE = pygame.K_g
_CHEAT_SPEED_BOOST = pygame.K_b
_CHEAT_EXTRA_LIFE = pygame.K_l
_CHEAT_SKIP_LEVEL = pygame.K_n

# Magenta cheat readout, matching the "42" wall colour so the active-cheats
# line reads as an obviously non-standard, debug overlay.
_CHEAT_COLOR = (255, 0, 255)


class GameDemo:
    """One playthrough: builds and coordinates every level, frame by frame."""

    # Declared here (without a value) so type checkers know the attribute types;
    # they are actually created inside _start_level(), which is why __init__
    # uses hasattr(self, "player") to detect the very first level build.
    player: Player
    grid: List[List[str]]
    pacgums: PacgumManager
    ghosts: GhostManager

    def __init__(self, screen: pygame.Surface, config: Config) -> None:
        """Set up the game and build level 1.

        Score and level live here (not on the player) because they must survive
        across levels while the player/pac-gums/ghosts get rebuilt each level.
        If maze generation fails, :attr:`failed` is set and ``update()`` returns
        ``True`` on the first frame so the menu loop takes the screen back.
        """
        self.screen = screen
        self.config = config
        self.maze = MazeLoader()

        self.score = 0
        self.level = 1
        self.victory_time: Optional[int] = None

        # Eating a super-pac-gum sets this deadline; the ghosts read it to know
        # they are edible.
        self.fright_until = 0

        self.hud_font = self._load_font(
            os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 24
        )

        # Task 9.1: the three TOGGLE cheats' on/off state. Extra-life and
        # level-skip are one-shot actions, not toggles. Set BEFORE
        # _start_level() runs because it re-applies the speed boost to each
        # freshly-built Player.
        self.cheat_invincible = False
        self.cheat_ghost_freeze = False
        self.cheat_speed_boost = False

        self.failed = not self._start_level()

    def _load_font(self, path: str, size: int) -> pygame.font.Font:
        """Load a font, exiting cleanly (no traceback) if the file is missing."""
        try:
            return pygame.font.Font(path, size)
        except FileNotFoundError:
            print(f"Error: font file '{path}' not found. Cannot start the game.")
            pygame.quit()
            sys.exit(1)

    def _start_level(self) -> bool:
        """Build one level (maze, player, pac-gums, ghosts). Return success.

        Called for level 1 from ``__init__`` and again every time a level is
        cleared or regenerated after a timeout. This is SETUP; per-frame logic
        lives in :meth:`update`/:meth:`draw`.
        """
        # Level 1 uses the fixed config seed (reproducible first maze); every
        # later level gets a random seed. Holds even when level 1 is
        # regenerated after a timeout, so retries stay reproducible too.
        if self.level == 1:
            seed = self.config.seed
        else:
            seed = 0

        # Task 6.2: config's "level" array can override the maze size for a
        # given level (1-indexed). Any level without a valid entry falls back
        # to the fixed MAZE_WIDTH/HEIGHT (procedural generation as before).
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

        grid = self.maze.generate(width, height, seed)
        if grid is None:
            # MazeLoader already printed the real error (Task 2.2).
            print("Error: could not generate the maze, returning to menu.")
            return False
        self.grid = grid

        cell, offset_x, offset_y = self.maze.get_layout(
            self.screen, self.grid, _HUD_HEIGHT
        )

        # Lives carry over between levels: the very first call pulls the
        # starting count from the config, every later call carries over
        # whatever the player currently has.
        if not hasattr(self, "player"):
            lives = self.config.lives
        else:
            lives = self.player.lives

        self.player = Player(
            self.screen, lives, self.grid, cell, offset_x, offset_y
        )
        # A fresh Player starts un-boosted, so re-apply the speed-boost cheat
        # if it is currently toggled on (e.g. after a level-skip).
        self.player.set_speed_boost(self.cheat_speed_boost)
        self.pacgums = PacgumManager(
            self.grid, self.player.current_cell(), cell, offset_x, offset_y
        )
        self.ghosts = GhostManager(
            self.screen, self.grid, cell, offset_x, offset_y
        )

        # "Ready" countdown before gameplay. Both player and ghosts stay frozen
        # until it ends. The level timer starts counting from the exact moment
        # this ends, not from construction.
        now = pygame.time.get_ticks()
        self.countdown_until = now + _READY_COUNTDOWN_MS
        self.level_start_time = self.countdown_until
        # Cleared so a fresh level never starts mid-freeze from a previous
        # attempt's timeout or ghost death.
        self.time_up_freeze_until: Optional[int] = None
        self.ghost_death_freeze_until: Optional[int] = None
        return True

    def _restart_level_in_place(self) -> None:
        """Reset positions after a ghost death WITHOUT rebuilding the maze.

        Unlike :meth:`_start_level`, this does not touch the grid or the
        pac-gums - only Pac-Man and the ghosts reset, then the normal "Ready"
        countdown runs again.
        """
        self.player.respawn()
        cell, offset_x, offset_y = self.maze.get_layout(
            self.screen, self.grid, _HUD_HEIGHT
        )
        self.ghosts = GhostManager(
            self.screen, self.grid, cell, offset_x, offset_y
        )
        self.fright_until = 0

        now = pygame.time.get_ticks()
        self.countdown_until = now + _READY_COUNTDOWN_MS
        self.level_start_time = self.countdown_until

    def is_pausable(self) -> bool:
        """Return ``True`` only during real play (not over a takeover screen).

        Not during the game-over/victory screens, and not on a failed level -
        pausing over a full-screen takeover would look broken.
        """
        return (
            not self.failed
            and not self.victory_time
            and not self.player.game_over_time
        )

    def shift_time(self, delta: int) -> None:
        """Slide every absolute deadline forward by ``delta`` ms (pause support).

        Every timer here is an absolute ``get_ticks()`` timestamp. Sliding them
        all forward by exactly the paused duration makes the pause consume zero
        game time, then fans the shift out to the player and the ghosts.
        """
        self.countdown_until += delta
        self.level_start_time += delta
        self.fright_until += delta
        if self.victory_time:
            self.victory_time += delta
        if self.time_up_freeze_until is not None:
            self.time_up_freeze_until += delta
        if self.ghost_death_freeze_until is not None:
            self.ghost_death_freeze_until += delta
        self.player.shift_time(delta)
        self.ghosts.shift_time(delta)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Apply any cheat key, then forward the event to the player.

        The cheat keys aren't arrow keys, so the player harmlessly ignores
        them; arrow keys never match a cheat.
        """
        if event.type == pygame.KEYDOWN:
            self._apply_cheat(event.key)
        self.player.handle_event(event)

    def _apply_cheat(self, key: int) -> None:
        """Map a pressed key to its cheat (toggle, one-shot, or ignore)."""
        if key == _CHEAT_INVINCIBLE:
            self.cheat_invincible = not self.cheat_invincible
        elif key == _CHEAT_GHOST_FREEZE:
            self.cheat_ghost_freeze = not self.cheat_ghost_freeze
        elif key == _CHEAT_SPEED_BOOST:
            self.cheat_speed_boost = not self.cheat_speed_boost
            self.player.set_speed_boost(self.cheat_speed_boost)
        elif key == _CHEAT_EXTRA_LIFE:
            self.player.lives += 1
        elif key == _CHEAT_SKIP_LEVEL:
            self._cheat_skip_level()

    def _cheat_skip_level(self) -> None:
        """Jump to the next level (or win, if already on the last one).

        Mirrors the "all pac-gums eaten" win branch in :meth:`update` so a
        skipped level behaves exactly like a genuinely cleared one.
        """
        if not self.is_pausable():
            return
        if self.level >= MAX_LEVEL:
            self.victory_time = pygame.time.get_ticks()
        else:
            self.level += 1
            if not self._start_level():
                self.failed = True

    def update(self) -> bool:
        """Advance the game one frame; return ``True`` when it should end."""
        # Maze generation failed in __init__ -> leave immediately, cleanly.
        if self.failed:
            return True

        # Has the 4-second victory screen finished showing?
        if self.victory_time:
            return pygame.time.get_ticks() - self.victory_time >= 4000

        # "Ready" countdown: nothing moves or ticks until it ends.
        if pygame.time.get_ticks() < self.countdown_until:
            return False

        # Task 6.1: time's up, frozen beat before retrying the SAME level in
        # place. Unlike a full rebuild, this keeps the maze and every already
        # eaten pac-gum (consumed gums do NOT respawn) - only positions reset.
        if self.time_up_freeze_until is not None:
            if pygame.time.get_ticks() < self.time_up_freeze_until:
                return False
            self.time_up_freeze_until = None
            self._restart_level_in_place()
            return False

        # Task 5.5: ghost caught Pac-Man, frozen beat before retrying in place.
        if self.ghost_death_freeze_until is not None:
            if pygame.time.get_ticks() < self.ghost_death_freeze_until:
                return False
            self.ghost_death_freeze_until = None
            self._restart_level_in_place()
            return False

        # Task 6.1 (CHANGED): per-level countdown timer. Running out of time
        # before the level is cleared now costs ONE life and retries the SAME
        # level in place - the maze and every already-eaten pac-gum are kept
        # (consumed gums do NOT respawn). Draining the last life is game over.
        # Checked BEFORE anyone moves this frame, so the freeze holds the exact
        # frame the timer expired. The game_over_time guard stops the expired
        # clock from re-triggering (and re-charging a life) every frame while
        # the game-over screen is showing.
        time_left_ms = (
            self.config.level_max_time * 1000
            - (pygame.time.get_ticks() - self.level_start_time)
        )
        if time_left_ms <= 0 and not self.player.game_over_time:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.player.game_over_time = pygame.time.get_ticks()
                return False  # game-over screen just triggered
            self.time_up_freeze_until = pygame.time.get_ticks() + _TIME_UP_FREEZE_MS
            return False

        # Player moves first; if the game-over screen is up this returns True
        # once it has been shown long enough.
        if self.player.update():
            return True
        if self.player.game_over_time:
            return False  # game-over screen still showing, skip the rest

        # Ghost update - chase, or flee while a super-pac-gum is active. The
        # ghost-freeze cheat skips their movement (they stay put but are still
        # drawn and still dangerous on contact).
        fright_remaining = self.fright_until - pygame.time.get_ticks()
        if not self.cheat_ghost_freeze:
            self.ghosts.update(self.player.current_cell(), fright_remaining)

        # Task 5.4: eating a frightened ghost.
        eaten_ghosts = self.ghosts.resolve_player_contact(self.player.x, self.player.y)
        self.score += eaten_ghosts * self.config.points_per_ghost

        # Task 5.5: real ghost contact - only CHASE-state ghosts are dangerous,
        # and the respawn invincibility window stops a hit chaining into
        # another death. The invincibility cheat also blocks the life loss.
        if (
            not self.cheat_invincible
            and not self.player.is_invincible()
            and self.ghosts.resolve_chase_contact(self.player.x, self.player.y)
        ):
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.player.game_over_time = pygame.time.get_ticks()
                return False  # game-over screen just triggered
            self.ghost_death_freeze_until = (
                pygame.time.get_ticks() + _GHOST_DEATH_FREEZE_MS
            )
            return False

        # Task 4.2: collection and scoring. Points only ever get ADDED.
        eaten = self.pacgums.collect(self.player.current_cell())
        if eaten == "PACGUM":
            self.score += self.config.points_per_pacgum
        elif eaten == "SUPER":
            self.score += self.config.points_per_super_pacgum
            # Ghosts become edible for 7 seconds.
            self.fright_until = pygame.time.get_ticks() + 7000

        # Task 4.3: level win condition.
        if self.pacgums.remaining() == 0:
            if self.level >= MAX_LEVEL:
                self.victory_time = pygame.time.get_ticks()
            else:
                self.level += 1
                if not self._start_level():
                    return True

        return False

    def draw(self) -> None:
        """Render the current frame (maze/sprites/HUD, or a takeover screen)."""
        if self.failed:
            return

        if self.victory_time:
            self._draw_center_text("You  Win!")
            return

        if self.player.game_over_time:
            self.player.draw()  # Player draws the Game Over screen itself
            return

        # "Ready" freeze: a plain black screen with a white countdown number.
        # The new level is fully built already but stays hidden until this ends.
        remaining_ms = self.countdown_until - pygame.time.get_ticks()
        if remaining_ms > 0:
            remaining_s = remaining_ms // 1000 + 1
            self._draw_center_text(str(remaining_s), color=(255, 255, 255))
            return

        # Draw order = layers: maze (kept clear of the top HUD strip), pac-gums,
        # ghosts, then Pac-Man on top, then the HUD and cheat overlay.
        self.maze.draw(self.screen, self.grid, _HUD_HEIGHT)
        self.pacgums.draw(self.screen)
        self.ghosts.draw(self.screen)
        self.player.draw()

        self._draw_hud()
        self._draw_cheats()

    def _draw_hud(self) -> None:
        """Draw score, level, lives and remaining time across the top strip.

        Because the layout reserves ``_HUD_HEIGHT`` at the top, the maze starts
        below this strip, so nothing here can ever overlap the maze.
        """
        time_left = max(
            0,
            self.config.level_max_time
            - (pygame.time.get_ticks() - self.level_start_time) // 1000,
        )
        items = [
            f"SCORE {self.score}",
            f"LEVEL {self.level}",
            f"LIVES {self.player.lives}",
            f"TIME {time_left}",
        ]
        screen_width = self.screen.get_width()
        # Give each item an equal horizontal slice and centre it within, so the
        # four readouts stay evenly spread at any screen width.
        slice_width = screen_width / len(items)
        for index, text in enumerate(items):
            surface = self.hud_font.render(text, False, (255, 255, 0))
            x = slice_width * index + (slice_width - surface.get_width()) / 2
            y = (_HUD_HEIGHT - surface.get_height()) / 2
            self.screen.blit(surface, (x, y))

    def _draw_cheats(self) -> None:
        """Draw a magenta line listing active cheats (nothing if none are on)."""
        active: List[str] = []
        if self.cheat_invincible:
            active.append("INVINCIBLE")
        if self.cheat_ghost_freeze:
            active.append("GHOST-FREEZE")
        if self.cheat_speed_boost:
            active.append("SPEED")
        if not active:
            return
        text = "CHEATS: " + "  ".join(active)
        surface = self.hud_font.render(text, False, _CHEAT_COLOR)
        y = self.screen.get_height() - surface.get_height() - 10
        self.screen.blit(surface, (10, y))

    def _draw_center_text(
        self, text: str, color: Tuple[int, int, int] = (255, 255, 0)
    ) -> None:
        """Draw a single large centred line on a black screen.

        Used for the Victory screen and, via ``color``, the white "Ready"
        countdown. Sized at 120 so longer text still fits on smaller screens.
        """
        font = self._load_font(
            os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 120
        )
        rendered = font.render(text, False, color)
        box = rendered.get_rect(
            center=(self.screen.get_width() / 2, self.screen.get_height() / 2)
        )
        self.screen.fill((0, 0, 0))
        self.screen.blit(rendered, box)
