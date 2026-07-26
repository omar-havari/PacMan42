*This activity has been created as part of the 42 curriculum by kbega, ohavari*

# Pac-Man

## Description

This project recreates the classic 1980 arcade game **Pac-Man** in Python, built
as a complete, playable game with an object-oriented, modular architecture.

The player moves through a procedurally-generated maze, eating pac-gums while
avoiding four autonomous ghosts. Eating a super-pac-gum (in each corner of the
maze) turns the ghosts blue and edible for a short time, letting the player eat
them for bonus points instead of losing a life to them. Clearing all pac-gums
wins the level; clearing 10 levels wins the game; running out of lives ends it.

The game includes a full menu system (main menu, pause menu, instructions,
highscores), a persistent JSON highscore table, a cheat mode for reviewers, and
a JSON configuration file (with comment support) that drives every tunable
value — lives, scoring, maze seed, per-level time limit, and more.

## Instructions

### Requirements
- Python 3.10+
- The dependencies listed in `requirements.txt` (pygame, and the assigned
  `mazegenerator` "A-Maze-ing" package, shipped as a local wheel in this repo
  since it isn't published on PyPI)

### Setup and run
```bash
make install    # creates venv/ and installs every dependency into it
make run         # launches the game with the default config.json
```

Or run it directly once dependencies are installed:
```bash
python3 pac-man.py config.json
```
The program takes **exactly one argument**: a path to a JSON configuration
file. Any error (missing file, invalid JSON, bad value) is handled cleanly with
a clear message — never a Python traceback.

### Other Makefile targets
| Target | What it does |
|---|---|
| `make debug` | Runs the game under Python's `pdb` debugger |
| `make clean` | Removes `__pycache__`, `.mypy_cache`, and `.pyc` files |
| `make lint` | Runs `flake8` + `mypy` (the required flags) over `src/`, the vendored maze package, and the root scripts |
| `make lint-strict` | Same, but with `mypy --strict` |

### Controls
| Key | Action |
|---|---|
| Arrow keys | Move Pac-Man |
| P / ESC | Pause / resume |
| Mouse click | Menu navigation |
| I / G / B / L / N | Cheat keys — see **Cheat mode** below |

### Packaging (for distribution)
```bash
pip install pyinstaller
pyinstaller pacman.spec
```
This produces a standalone build in `dist/pacman/` that bundles the assets,
default config, and in-package instructions (`CONTROLS.txt`) — no Python
installation required to run it.

## Resources

### References
- [Pac-Man (Wikipedia)](https://en.wikipedia.org/wiki/Pac-Man) — original game history and ghost behavior (Blinky/Pinky/Inky/Clyde)
- [pygame documentation](https://www.pygame.org/docs/) — the graphics/input/audio library used for the game
- [Python `typing` module docs](https://docs.python.org/3/library/typing.html) and [mypy documentation](https://mypy.readthedocs.io/) — for the type-hinting/static-checking requirement
- [PyInstaller documentation](https://pyinstaller.org/) — used to package the game into a standalone build
- [Itch.io butler docs](https://itch.io/docs/butler/) — used to upload the packaged build

### AI usage disclosure
AI (Claude) was used throughout development as a coding assistant, across most
implementation tasks: building out the ghost AI (chase/flee/eaten states),
collision detection (including diagnosing and fixing a grid-quantization
"tunneling" bug where fast head-on collisions could be missed), the per-level
countdown/timeout/respawn-freeze flow, speed tuning, the cheat mode, the pause
system, packaging/deployment guidance, a project-wide compliance review against
the subject, and diagnosing/fixing a corrupted git merge that had left literal
conflict markers inside two source files. Every AI-suggested change was
reviewed, tested (including headless simulation of edge cases such as the
collision-detection fix), and understood by the author before being accepted;
none of it was copy-pasted without verification.

## Configuration

The game is configured via a JSON file (comments starting with `#` are
stripped before parsing). Any missing key falls back to a safe default, any
invalid value is clamped to its default with a warning printed to the console,
and unknown keys are silently ignored — the game never crashes on a bad
config.

| Key | Default | Meaning |
|---|---|---|
| `highscore_file` | `"highscores.json"` | Path to the persistent highscore file |
| `level` | `[]` | Optional array of `{"width": w, "height": h}` overrides, one per level (1-indexed). Any level without an entry (or once the array runs out) falls back to the default 15×15 maze |
| `width`, `height` | `800`, `600` | Window size in pixels |
| `lives` | `3` | Starting lives |
| `points_per_pacgum` | `10` | Score for eating a pac-gum |
| `points_per_super_pacgum` | `50` | Score for eating a super-pac-gum |
| `points_per_ghost` | `200` | Score for eating a frightened ghost |
| `seed` | `42` | Fixed seed for level 1's maze (reproducible); levels 2+ always use a fresh, genuinely random seed regardless of this value |
| `level_max_time` | `160` | Seconds allowed to clear each level before it resets |

`config.json` at the repo root is the default/example configuration.

## Highscore

Highscores are stored as a JSON file (path from the config's
`highscore_file` key, `highscores.json` by default) at the project root. This
format was chosen because it needs no external database, is human-readable,
and is trivial to make robust: `HighscoreManager` is the *only* code that ever
touches the file, so the format lives in exactly one place.

- Only the top 10 scores are kept, sorted descending.
- Names are validated (1–10 characters, letters/digits/spaces only); scores
  are validated (non-negative integers). Anything else is silently rejected
  rather than corrupting the table.
- A missing file (first run) or a corrupted/unreadable file never crashes the
  game — it just starts from an empty table and warns.
- Scores are loaded once at game/menu start and saved immediately whenever a
  new entry is added (right after the player enters their name on the
  Game Over or Victory screen).
- The top scores are previewed on the main menu, with a full ranked top-10
  screen available from the "View Highscores" button.

## Maze Generation

Mazes are generated by the assigned external **A-Maze-ing** package
(`mazegenerator`), used exactly as provided — it is never modified, and is
installed from the wheel vendored in this repo
(`mazegenerator-00001-py3-none-any.whl`) since it isn't on PyPI.

`MazeLoader` (in `src/maze_loader.py`) adapts the package's compact output (a
grid of per-cell wall bitmasks) into the expanded `WALL`/`CORRIDOR` grid the
rest of the game works with, always calling the generator with `PERFECT=False`
as required. Cells the generator marks as part of its hidden "42" easter egg
become a distinct, always-solid wall type so they render differently and are
never mistaken for a walkable corridor. If the generator raises an exception
for any reason, the error is caught and logged cleanly — the game returns to
the main menu instead of crashing.

**Seeding:** level 1 always uses the config's fixed `seed`, so its maze is
reproducible. Every later level must be genuinely random — this needed a
specific fix, because the generator reseeds Python's own global `random`
module internally (`random.seed(seed)`). Since level 1 always seeds it with
the same fixed value, drawing a "random" seed from that same global state
right afterward was actually fully deterministic across every run. The fix:
pass `seed = 0` for level 2+, which makes the generator reseed itself from
real OS entropy instead, giving genuinely different mazes on every playthrough.

## Implementation

A few of the more notable technical choices:

- **Movement** is cell-snapped: sprites travel from cell-centre to
  cell-centre, and only change direction or stop at a wall exactly when
  aligned to a grid boundary. Speed is tuned by taking multiple *whole*
  base-speed steps per frame (never a bigger single step), so it can be
  increased freely without ever risking a sprite stepping past an alignment
  point. An additional global speed multiplier (`SPEED_SCALE` in
  `movement.py`) is applied via a fractional duty-cycle accumulator — it
  scales overall pace by skipping a proportion of frames evenly, rather than
  changing step size, so alignment is never at risk regardless of the chosen
  multiplier.
- **Ghost AI** is a simple, distance-based greedy chase: at each intersection
  a ghost picks whichever legal direction minimizes squared distance to
  Pac-Man (or maximizes it, when frightened) — deliberately simple over a
  full pathfinding search, as recommended by the subject.
- **Collision detection** between Pac-Man and ghosts uses pixel
  bounding-box overlap, not exact grid-cell equality. Cell-equality was found
  to occasionally miss a fast head-on pass entirely (two sprites crossing
  near a cell boundary within one frame could swap sides without ever landing
  in the same quantized cell) — pixel overlap has a much wider detection
  window and closes that gap.
- **Screens** are driven by one single main loop (`src/app.py`) dispatching on
  a `GameState` enum, rather than each screen owning its own blocking loop.
- Level starts (and retries after a ghost catches Pac-Man, or the level timer
  running out) go through a brief frozen "Ready" countdown so ghosts never
  get a head start over a player who hasn't moved yet.

## General Software Architecture

```
pac-man.py            CLI entry point: validates args, loads Config, launches the app
src/
  app.py              App: the single main loop, dispatches to the active screen by GameState
  game_state.py        GameState: which screen is currently active
  config.py            Config: loads and validates config.json
  resources.py          Resolves asset/config paths for both source and packaged runs
  maze_loader.py        MazeLoader: wraps `mazegenerator`, builds and draws the WALL/CORRIDOR grid
  movement.py           Shared grid-movement helpers (alignment, directions, speed) used by both Player and Ghost
  Player.py             Player: Pac-Man's movement, animation, lives, respawns
  ghost.py              Ghost / GhostManager: chase/flee/eaten AI and rendering, for all 4 ghosts
  pacgums.py            PacgumManager: places, tracks, and draws pac-gums/super-pac-gums
  pacman_images.py      ImageElement: small helper for loading/positioning a static image
  GameDemo.py           GameDemo: the in-game screen — coordinates maze/player/ghosts/pac-gums/scoring/HUD/cheats/pause each frame
  highscore.py          HighscoreManager: the persistent JSON highscore store
  screens.py            MainMenu, HighscoresScreen, InstructionsScreen, NameEntryScreen, PauseMenu
```

`GameDemo` is the only class that talks to `Player`, `GhostManager`, and
`PacgumManager` directly — each of those, in turn, is the sole owner of its
own piece of state (position/lives, ghost AI, pac-gum placement), so no two
classes disagree about the same data. `MazeLoader` and `movement.py` are
shared utilities with no game-rule knowledge of their own.

## Project Management

Project management artifacts (progress tracking, risk analysis, and blocking
points encountered during development) are kept in the
[`project-management/`](project-management/) directory.
