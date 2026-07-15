import os
import random
import sys

import pygame

from src.Player import Player
from src.maze_loader import MazeLoader
from src.pacgums import PacgumManager

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

# Maze size in GENERATOR cells - the expanded WALL/CORRIDOR grid on screen
# is (2*w+1) x (2*h+1), so 15x15 becomes a 31x31 grid. Later the config's
# "level" array can override this per level.
MAZE_WIDTH = 15
MAZE_HEIGHT = 15
MAX_LEVEL = 10  # subject: the game is won after completing 10 levels


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

    # NEW (Task 4.3): builds one level - maze, player, pacgums. Called for
    # level 1 from __init__ and again every time a level is cleared.
    def _start_level(self):
        # Subject rule: level 1 uses the fixed seed from the config (so the
        # first maze is reproducible), every later level gets a random seed.
        if self.level == 1:
            seed = self.config.seed
        else:
            seed = random.randrange(1_000_000)

        self.grid = self.maze.generate(MAZE_WIDTH, MAZE_HEIGHT, seed)
        if self.grid is None:
            # MazeLoader already printed the real error (Task 2.2).
            print("Error: could not generate the maze, returning to menu.")
            return False

        cell, offset_x, offset_y = self.maze.get_layout(self.screen, self.grid)

        # Lives carry over between levels: on level 1 they come from the
        # config, afterwards from the player that just cleared the level.
        if self.level == 1:
            lives = self.config.lives
        else:
            lives = self.player.lives

        self.player = Player(self.screen, lives, self.grid, cell, offset_x, offset_y)
        self.pacgums = PacgumManager(
            self.grid, self.player.current_cell(), cell, offset_x, offset_y
        )
        return True

    def handle_event(self, event):
        self.player.handle_event(event)

    def update(self):
        # Maze generation failed in __init__ -> leave immediately, cleanly.
        if self.failed:
            return True

        # --- has the 4-second victory screen finished showing? ---
        if self.victory_time:
            return pygame.time.get_ticks() - self.victory_time >= 4000

        # Player moves first; if the game-over screen is up this returns
        # True once it has been shown long enough.
        if self.player.update():
            return True
        if self.player.game_over_time:
            return False  # game-over screen still showing, skip the rest

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

        # Draw order = layers: maze fills the background, pacgums sit in
        # the corridors, pacman on top, HUD text above everything.
        self.maze.draw(self.screen, self.grid)
        self.pacgums.draw(self.screen)
        self.player.draw()

        # Task 4.2: live score display (a proper HUD comes in Phase 8).
        hud = self.hud_font.render(
            f"Score {self.score}  Level {self.level}  Lives {self.player.lives}",
            False,
            (255, 255, 0),
        )
        self.screen.blit(hud, (10, 10))

    # NEW: victory screen, same style as the Game Over screen. Sized at 120
    # (not 300) so the longer text still fits on smaller screens.
    def _draw_center_text(self, text):
        font = self._load_font(
            os.path.join(_ASSETS, 'fonts', 'PressStart2P-Regular.ttf'), 120
        )
        rendered = font.render(text, False, (255, 255, 0))
        box = rendered.get_rect(
            center=(self.screen.get_width() / 2, self.screen.get_height() / 2)
        )
        self.screen.fill((0, 0, 0))
        self.screen.blit(rendered, box)
