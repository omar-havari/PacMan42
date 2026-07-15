# /plan — Phase 5, Task 5.1: Ghost base class and spawning

## Where the project stands right now

Per `TASK_PLAN.md`, Phases 0–4 are done on branch `Keidi-Pacman`:

- **Phase 2** — maze generation is wired up (`MazeLoader` in `src/maze_loader.py`).
- **Phase 3** — `Player` (`src/Player.py`) has cell-snapped movement, wall
  collision, spawn/respawn at the maze centre, and a lives/game-over system.
- **Phase 4** — `PacgumManager` (`src/pacgums.py`) places and tracks pacgums,
  `GameDemo` (`src/GameDemo.py`) handles scoring and level-win/level-advance.

The next unchecked box in `TASK_PLAN.md` is **Phase 5, Task 5.1 — Ghost base
class and spawning**:

```
- [ ] Create `Ghost` class with position, speed, state (CHASE/FLEE/EATEN)
- [ ] Spawn 4 ghosts, one per maze corner
- [ ] Load the 4 ghost sprite images you already have (pink, orange, cyan, red)
- [ ] Implement basic corridor-constrained movement (same wall logic as player)
```

This document is the plan for **that task only**. Tasks 5.2–5.5 (chase, flee,
eaten/respawn, real collision) build on top of it and get their own plan once
5.1 is merged — trying to design all five at once is how the "ghosts" phase
turns into an unreviewable wall of code.

---

## What we already have that this task reuses

The whole point of this plan is: **almost nothing here is new**. Phase 3 already
solved "an actor that lives on the grid and can't walk through walls" once,
for `Player`. A ghost is the same actor with a different brain.

| Need | Already exists as | File | Reuse plan |
|---|---|---|---|
| The maze grid (`"WALL"`/`"CORRIDOR"`/`"FT_WALL"`) | `self.grid` | `GameDemo.py:67` | Pass the *same* `self.grid` object into the ghost code — do not regenerate or copy it. |
| Cell size + screen offsets | `get_layout()` | `maze_loader.py:61` | Already computed once in `_start_level` (`GameDemo.py:73`) — pass the same `cell, offset_x, offset_y` into ghosts, exactly like `Player` and `PacgumManager` already receive them. This is what guarantees ghosts line up with the same walls Pac-Man does. |
| Direction vectors (`(dx, dy)` per direction) | `_DIRECTIONS` dict | `Player.py:10-15` | Reuse as-is (see "Shared movement code" below) — a ghost needs the exact same North/East/South/West → `(dx,dy)` mapping. |
| "Is the cell in direction X a corridor?" | `_can_go()` | `Player.py:101-109` | Same check, same logic — a ghost cannot enter `"WALL"`/`"FT_WALL"` tiles any more than Pac-Man can. |
| "Which grid cell am I standing in?" | `current_cell()` | `Player.py:93-96` | Same pixel→cell math. Needed for both movement decisions and, later, ghost↔player collision detection (Task 5.5). |
| "Am I exactly aligned with the grid?" | the `aligned` check in `update()` | `Player.py:153-156` | A ghost needs this too — it can only choose a new direction (chase/flee/random) at a cell boundary, otherwise it visually clips through corners. |
| Speed that evenly divides `cell` | the `for candidate in range(...)` loop | `Player.py:51-54` | Reuse verbatim — same reasoning applies (a speed that doesn't divide `cell` breaks the alignment check for anyone using it). |
| A per-level "owns a list of N things built from the grid" manager | `PacgumManager` | `src/pacgums.py` | This is the structural template for the new `GhostManager` — see below. |
| Ghost-edible timer | `self.fright_until` | `GameDemo.py:39`, set at `GameDemo.py:116` | Already ticking on super-pacgum pickup (Task 4.2), currently read by nobody. Task 5.1 doesn't need it yet (that's Task 5.3), but the ghost's `update()` should be written expecting to receive it — don't invent a second timer. |
| Score for eating a ghost | `config.points_per_ghost` | `config.py` (parsed already) | Not used in 5.1, but confirms the config side is already done for Task 5.4 — nothing to add there. |
| Losing a life | `Player.lose_life()` | `Player.py:212-219` | Fully implemented, currently has **zero callers** (dead code waiting for Task 5.5). Task 5.1 doesn't call it yet — just noting it's ready. |

### Shared movement code — one real design decision in this task

`Player._DIRECTIONS`, `_OPPOSITE`, the alignment check, and `_can_go()` are
currently private to `Player.py`. A `Ghost` needs the identical logic. Two
options:

1. **Duplicate** the four lines into `Ghost` (fast, but now wall-collision
   logic exists in two places that can drift apart).
2. **Extract** `_DIRECTIONS`, `_OPPOSITE`, and a standalone `is_corridor(grid,
   row, col)` helper into a small shared module (e.g. `src/movement.py`), and
   have both `Player` and `Ghost` import from it.

**Recommendation: option 2.** The project's own notes already flag "modular,
reusable architecture" as a grading requirement (see `TASK_PLAN.md` Task
3.1), and this is exactly the kind of duplication that requirement is meant
to prevent — four ghosts and one player all doing wall-collision math is the
textbook case for one shared function instead of five copies. This is a
small, mechanical extraction (move code, don't rewrite it) and is step 1
below for that reason.

### The one real gap: ghost sprites

`TASK_PLAN.md` says "load the 4 ghost sprite images you already have (pink,
orange, cyan, red)." Checking `assets/images/`, only **one** ghost-shaped
image currently exists:

```
Screenshot_From_2026-07-10_12-31-49-removebg-preview.png
```

(The other recent addition, `...12-32-10...`, is the cigarette-pack sprite
already used as the super-pacgum in `pacgums.py:63-66` — not a ghost.)

This needs a decision before or during 5.1:
- **(a)** generate/export 3 more ghost images in the other colors, or
- **(b)** load the single sprite once and re-tint it 4 ways in code (pygame
  can multiply a surface's colour with `BLEND_RGBA_MULT`), or
- **(c)** ship with 4 ghosts sharing one sprite for now and treat distinct
  colors as a follow-up polish item.

Not blocking for writing the `Ghost` class itself — just flagging it so it
doesn't get discovered mid-task. Recommend (b) if new art isn't readily
available: it's a few lines in `_load_sprite`-style code you already have a
pattern for (`pacgums.py:68-75`).

---

## Step-by-step build order

### Step 1 — Extract the shared movement helper
Create `src/movement.py` (or similar) holding `DIRECTIONS`, `OPPOSITE`, and a
free function `is_corridor(grid, row, col)`. Update `Player.py` to import
from it instead of defining its own copies; confirm the game still runs
identically (this step changes zero behavior, only where the code lives).

### Step 2 — Create `src/ghost.py` with the `Ghost` class
Mirror `Player.__init__`'s signature shape: `(screen, grid, cell, offset_x,
offset_y, spawn_cell, color)`. Reuse, don't reinvent:
- the speed-picking loop (`Player.py:51-54`)
- `current_cell()` (`Player.py:93-96`)
- the aligned-check + `_can_go()` pattern (`Player.py:101-109`, `153-161`),
  now calling the shared `is_corridor()` from Step 1

State for this task is just an enum/string: `"CHASE"` (the only state 5.1
needs — `"FLEE"`/`"EATEN"` are stored but unused until Tasks 5.3/5.4, so the
attribute exists now but nothing sets it to anything but `"CHASE"` yet).

Movement direction for 5.1 can be as simple as "pick a random open direction
at each alignment point, never immediately reverse unless it's a dead end" —
real chase logic is Task 5.2, not this task. Keep 5.1's movement dumb on
purpose so it's easy to verify ghosts obey walls before adding any AI.

### Step 3 — Corner spawn positions
The four maze corners are already a solved problem — `PacgumManager` computes
them for super-pacgums:

```python
# pacgums.py:39-44
corners = [
    (1, 1),
    (1, cols - 2),
    (rows - 2, 1),
    (rows - 2, cols - 2),
]
```

`GhostManager` (Step 4) should compute the same four `(row, col)` pairs the
same way — odd-odd indices are guaranteed corridors by construction (see
`Maze_Code_Reference.md` section 3), so no searching/validation is needed,
exactly as the pacgum code already assumes.

### Step 4 — Create `GhostManager` in the same file, using `PacgumManager` as the template
Compare shapes directly:

```python
# existing pattern (pacgums.py:14)
class PacgumManager:
    def __init__(self, grid, start_cell, cell, offset_x, offset_y):
        ...
    def draw(self, screen): ...

# new, same shape
class GhostManager:
    def __init__(self, grid, cell, offset_x, offset_y):
        self.ghosts = [Ghost(..., spawn_cell=c, color=col)
                        for c, col in zip(corner_cells, colors)]
    def update(self):
        for g in self.ghosts: g.update()
    def draw(self, screen):
        for g in self.ghosts: g.draw(screen)
```

One `update()`/`draw()` pair that loops over all 4 ghosts, so `GameDemo`
only ever talks to one object — same reason `GameDemo` talks to one
`PacgumManager` instead of N pacgum objects directly.

### Step 5 — Wire into `GameDemo._start_level()`
Same place, same pattern as the existing pacgum wiring:

```python
# GameDemo.py:82-85, current
self.player = Player(self.screen, lives, self.grid, cell, offset_x, offset_y)
self.pacgums = PacgumManager(
    self.grid, self.player.current_cell(), cell, offset_x, offset_y
)

# add directly after, same shape
self.ghosts = GhostManager(self.grid, cell, offset_x, offset_y)
```

Then in `update()` (`GameDemo.py:91`) add `self.ghosts.update()` alongside
the existing `self.player.update()` call, and in `draw()` (`GameDemo.py:130`)
add `self.ghosts.draw(self.screen)` — put it **before** `self.player.draw()`
(`GameDemo.py:146`) so Pac-Man renders on top of ghosts, matching the
existing layering comment at `GameDemo.py:142-143`.

Do **not** add collision-with-player logic yet — that is Task 5.5, and
bolting it on early means testing 5.1 (do ghosts move and respect walls?)
gets tangled up with testing something Phase 5.1 isn't responsible for yet.

### Step 6 — Verify
Per the project's usual verification approach (headless pygame, no display
needed):

```bash
SDL_VIDEODRIVER=dummy ./venv/Scripts/python.exe -c "
import sys; sys.path.insert(0, '.')
from src.config import Config
from src.GameDemo import GameDemo
import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
game = GameDemo(screen, Config('config.json'))
for _ in range(300):
    game.update()
print('ghost cells:', [g.current_cell() for g in game.ghosts.ghosts])
print('all on corridor:', all(game.grid[r][c] == 'CORRIDOR' for r, c in
      (g.current_cell() for g in game.ghosts.ghosts)))
"
```
Confirms: 4 ghosts spawned, none crashed the game loop over 300 frames, and
every ghost is always standing on a `"CORRIDOR"` tile (never inside a wall).

---

## After this task: what Phase 5 still needs

Once 5.1 is in, in order:

- **5.2 Chase** — replace the "random direction" placeholder from Step 2 with
  distance-based direction choice toward `player.current_cell()`.
- **5.3 Flee** — read `GameDemo.fright_until` (already ticking, see the table
  above) to switch ghosts into `"FLEE"` and move away from the player instead
  of toward it.
- **5.4 Eaten + respawn** — collision with a `"FLEE"` ghost → `"EATEN"` state,
  `+= config.points_per_ghost`, timed respawn at its corner.
- **5.5 Real collision** — collision with a `"CHASE"` ghost finally calls the
  already-written `Player.lose_life()`.

Each of those is a small, focused change on top of the `Ghost`/`GhostManager`
skeleton this task builds — which is exactly why keeping 5.1 to "just move
and don't hit walls" matters.
