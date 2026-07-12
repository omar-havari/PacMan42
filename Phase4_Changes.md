# Phase 4 — Explained In Depth

This document re-explains everything that changed for Phase 4, slowly, with
diagrams and real numbers. Read it top to bottom — each section builds on the
one before it.

**Files touched:**

| File | What happened |
|---|---|
| `src/maze_loader.py` | small additions: `get_layout()`, the magenta "42" |
| `src/Player.py` | big rewrite: pacman now lives inside the maze |
| `src/pacgums.py` | brand new file: all pacgum logic |
| `src/GameDemo.py` | big rewrite: it became the real game screen |

---

## Part 0 — The problem we had to solve first

Before Phase 4, the game looked like this:

- `test_maze.py` could draw a maze… **in its own separate window, disconnected
  from the game.**
- The actual game (`GameDemo`) knew *nothing* about mazes. Pacman flew around
  an empty black screen, and "game over" meant "you left the screen".

Phase 4 is "put pacgums in the corridors and eat them". You can't do that when
the game has no corridors. So before any pacgum code could be written, the maze
had to be moved *into* the game, and pacman had to learn to respect walls
(that was Task 3.2/3.3 in the plan — it was never finished, so it got finished
now).

Keep this in mind while reading: **about half the changes are that missing
glue, and the other half is actual Phase 4.**

---

## Part 1 — How positions work now (the foundation for everything)

### 1.1 Two coordinate systems

Everything in Phase 4 depends on understanding that there are now **two ways to
describe "where something is"**:

1. **Grid coordinates** `(row, col)` — which *cell* of the maze you're in.
   Row 0 is the top row. Used for logic: "is there a wall?", "is there a
   pacgum here?"
2. **Pixel coordinates** `(x, y)` — where on the *screen* something is drawn.
   Used only for drawing and smooth movement between cells.

The whole trick of Phase 4 is converting between the two correctly, and making
sure *every* piece of code converts the same way.

### 1.2 The maze grid

`MazeLoader.generate(15, 15, seed)` returns a 2D list of strings, 31 rows ×
31 columns. Why 31? The generator works with 15×15 "rooms", and between every
two rooms there may or may not be a wall. To show that on screen, each room
becomes a cell, and each *potential wall between rooms* also becomes a cell:

```
15 rooms + 16 wall slots between/around them = 31 cells per side
```

Each entry in the grid is one of three strings:

- `"WALL"` — solid, blue outline, you can't enter it
- `"CORRIDOR"` — walkable, this is where pacgums go
- `"FT_WALL"` — NEW: the cells forming the "42" in the middle. Solid like a
  wall, but drawn magenta (explained in Part 5)

A useful fact you'll see used twice later: because rooms sit at positions
1, 3, 5, … in the expanded grid, **every cell with odd row AND odd column is
guaranteed to be walkable**. Wall cells only exist at even rows/columns.

### 1.3 `get_layout()` — one source of truth for the geometry

To draw the grid on screen, three numbers are needed:

- `cell` — how many pixels one grid cell is
- `offset_x`, `offset_y` — the empty margins that centre the maze on screen

Example with real numbers, fullscreen 1920×1080:

```
cell     = min(1920 // 31, 1080 // 31) = min(61, 34) = 34 pixels
maze is 31 * 34 = 1054 pixels wide/tall
offset_x = (1920 - 1054) // 2 = 433   <- big margins left/right
offset_y = (1080 - 1054) // 2 = 13    <- almost no margin top/bottom
```

**Before**, these three numbers were calculated as local variables *inside*
`MazeLoader.draw()`. That was fine when only drawing needed them. But now:

- the **player** needs them (to know which pixel = which cell, for collision)
- the **pacgums** need them (to be drawn in the middle of the right cell)

If each of those recomputed the numbers themselves and one of them was ever
changed slightly, the walls you *see* and the walls you *collide with* would
silently drift apart. So the calculation moved into a method:

```python
cell, offset_x, offset_y = maze.get_layout(screen, grid)
```

and now `draw()`, `Player`, and `PacgumManager` all call/receive the exact
same numbers. That's the entire change to the layout code — same math, new
home.

### 1.4 Converting between pixels and cells

With those numbers, conversion is just multiplication/division:

```
pixel position of cell (row, col):
    x = offset_x + col * cell
    y = offset_y + row * cell

cell containing pixel (x, y):
    col = (x - offset_x) // cell
    row = (y - offset_y) // cell
```

Worked example (1920×1080, so cell=34, offset_x=433):
cell (15, 15) starts at pixel x = 433 + 15·34 = **943**. And pixel x=950 is in
column (950−433)//34 = 517//34 = **15**. ✓ Round trip works.

One subtlety: `Player.current_cell()` doesn't convert pacman's top-left corner
— it converts his **centre** (`x + cell//2`). Why? While pacman slides from
cell A to cell B, his sprite overlaps both. Using the centre means "which cell
is he *mostly* in", so the answer only flips when he's really halfway across.
This matters for eating pacgums: the pacgum disappears exactly when pacman's
body is on top of it, not when his nose first touches the cell.

---

## Part 2 — `Player.py`: the movement rewrite

### 2.1 What it was before

```python
if self.direction == "right":
    self.x += self.speed          # speed was always 3
```

Every frame, move 3 pixels in whatever direction was last pressed. No walls
existed, so nothing ever stopped you. Pressing an arrow key changed direction
*instantly*, anywhere.

### 2.2 The choice: how should walls stop you?

Task 3.2 offered two options:

**Option A — free movement + collision check:** keep pixel movement, and each
frame check "would my rectangle overlap a wall? then don't move." Sounds
simple, but plays *horribly* in a maze with corridors exactly 1 cell wide: to
turn into a side corridor you'd have to be pixel-perfectly aligned with it.
You'd constantly bump against corners and get stuck on edges.

**Option B — cell-snapped movement (what we chose, and what the real arcade
game does):** pacman is only ever allowed to be *on the line of the grid*. He
travels from cell centre to cell centre, and decisions (turn / stop) happen
only at the moments he's exactly on a cell boundary. Turning is then always
clean, and he's always perfectly centred in a corridor.

### 2.3 The three pieces that make cell-snapping work

**Piece 1 — `wanted_direction` (the "wish").**

Before: arrow key → `self.direction` changes immediately.
Now: arrow key → only `self.wanted_direction` changes. Actual turning is
decided in `update()`.

Why? Imagine pacman moving right down a corridor, and you press ↓ slightly
*before* the junction. Instantly turning down would slam him into the wall
below the corridor. Instead, the wish is *remembered*, and at the next moment
he's aligned with the grid AND the cell below is a corridor, the wish is
applied. This is exactly the arcade behaviour: you press the turn early, and
pacman takes it at the next junction. It makes the game feel responsive
instead of frustrating.

**Piece 2 — the alignment check.**

```python
aligned = ((self.x - offset_x) % self.cell == 0 and
           (self.y - offset_y) % self.cell == 0)
```

Translation: "after removing the margin, is my pixel position an exact
multiple of the cell size?" — i.e. "am I sitting exactly on a cell, not
between two cells?"

Worked example (cell=34, offset_x=433): pacman at x=943.
(943−433) % 34 = 510 % 34 = 0 → aligned ✓. Two frames later at x=947:
514 % 34 = 4 → not aligned, no turning allowed, keep sliding.

Only when `aligned` is true do these two things happen:

```python
if self.wanted_direction and self._can_go(self.wanted_direction):
    self.direction = self.wanted_direction     # take the turn
if self.direction and not self._can_go(self.direction):
    self.direction = None                      # wall ahead -> stop
```

That second line **is the entire wall collision system.** There is no
rectangle-overlap math anywhere. Movement simply never *starts* toward a wall,
so pacman can never be inside one.

**Piece 3 — `_can_go(direction)`: "is the neighbouring cell walkable?"**

```python
dx, dy = _DIRECTIONS[direction]      # e.g. "right" -> (1, 0)
row, col = self.current_cell()
return grid[row + dy][col + dx] == "CORRIDOR"
```

`_DIRECTIONS` is a new dictionary at the top of the file:

```python
_DIRECTIONS = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}
```

It turns a direction *name* into a step. Before, every function that cared
about direction had its own 4-branch `if/elif`. With the dictionary, moving is
just `self.x += dx * self.speed` — one line for all four directions. Note that
because `FT_WALL` is not `"CORRIDOR"`, the magenta 42 blocks movement
automatically, with zero extra code.

**The one exception: the 180° turn.** Reversing (right→left, up→down) is
allowed *immediately*, even between cells — because the cell behind pacman is
the one he just came from, so it's guaranteed walkable. The `_OPPOSITE`
dictionary exists just for this check. Without this exception, reversing would
feel laggy (you'd wait up to a full cell before turning back).

### 2.4 Why the speed formula looks weird

```python
self.speed = 1
for candidate in range(max(1, cell // 6), 0, -1):
    if cell % candidate == 0:
        self.speed = candidate
        break
```

This finds the **largest number ≤ cell/6 that divides the cell size evenly**.

Why must speed divide the cell size? The alignment check tests
`position % cell == 0` — an *exact* equality. Pacman moves `speed` pixels per
frame, so his positions are `0, speed, 2·speed, …`. If speed doesn't divide
`cell`, he *steps over* the exact boundary and never lands on it:

```
cell = 34, speed = 4:  positions 28, 32, 36 ... 34 is skipped!
   -> "aligned" is never true again -> can never turn, never stops at walls
cell = 34, speed = 2:  positions 30, 32, 34 ✓ lands exactly on the boundary
```

The old fixed `speed = 3` would break on most screen sizes. The `cell // 6`
cap just keeps the speed reasonable (~1/6 of a cell per frame ≈ 10 cells/sec
at 60fps).

### 2.5 Spawning and respawning (Task 3.3)

```python
row = len(grid) // 2      # 31 // 2 = 15
col = len(grid[0]) // 2   # 15
```

The centre cell of a 31×31 grid is (15, 15) — odd row, odd column — and
remember from Part 1.2: **odd/odd cells are always corridors.** So spawning at
the exact centre is guaranteed safe, with no searching and no hardcoding.
`lose_life()` now calls this same `respawn()` (before, it reset to the *screen*
centre, which after the maze integration could have been inside a wall).

### 2.6 Smaller changes

- Frames scale to `(cell, cell)` instead of a fixed 150×150 — pacman must fit
  a corridor whatever the resolution.
- The mouth animation only advances **while moving** — a stopped pacman no
  longer chews the air.
- The "left the screen → lose a life" checks were **deleted**: the maze's
  border is an unbroken ring of walls, so leaving the screen is impossible.
  From now on, lives are lost to ghosts (Phase 5) — which is why nothing
  currently calls `lose_life()`.
- `draw()` **no longer fills the screen black.** Before, the player was the
  whole scene, so it cleared the screen itself. Now the maze is drawn first
  and fills the background; if the player cleared the screen afterwards, the
  maze would vanish. Draw order lives in `GameDemo.draw()` now (Part 4.4).

---

## Part 3 — `pacgums.py`: the new file (Tasks 4.1 + 4.2)

### 3.1 Why a separate class at all?

`GameDemo` shouldn't have to know where 450+ dots are and how to draw each
kind. `PacgumManager` hides all of it behind three questions:

- `collect(cell)` → "the player is standing here — did he just eat something,
  and what?"
- `remaining()` → "how many are left?" (for the win condition)
- `draw(screen)` → "draw yourselves"

### 3.2 How the pacgums are stored — and why a dict

```python
self.pacgums = {}                    # (row, col) -> "PACGUM" or "SUPER"
self.pacgums[(3, 7)] = "PACGUM"      # example entry
```

The alternative would have been writing `"PACGUM"` into the maze grid itself.
The dict is better for three concrete reasons:

1. **Eating is one line.** `dict.pop(key, default)` means "remove this key and
   give me its value; if it isn't there, give me the default instead of
   crashing":

   ```python
   def collect(self, cell_pos):
       return self.pacgums.pop(cell_pos, None)
   ```

   Called every frame with pacman's current cell. Almost every frame the cell
   is already empty → returns `None`, nothing happens. The one frame pacman
   enters a full cell → returns `"PACGUM"` or `"SUPER"` **and** removes it in
   the same operation, so it can't ever be eaten (scored) twice.

2. **The win condition is one line:** `len(self.pacgums) == 0`.

3. **The maze grid stays purely about walls.** Collision code never has to ask
   "is `PACGUM` walkable too?"

### 3.3 Placement (Task 4.1)

```python
for r in range(rows):
    for c in range(cols):
        if grid[r][c] == "CORRIDOR" and (r, c) != start_cell:
            self.pacgums[(r, c)] = "PACGUM"
```

A dot in *every* corridor cell, with one exception: the player's starting
cell — otherwise he'd be awarded points on frame 1 while standing still.
(And note: `FT_WALL` cells are not `"CORRIDOR"`, so the 42 gets no pacgums —
that detail matters in Part 5.)

Then the four **super-pacgums** overwrite the corners:

```python
corners = [(1, 1), (1, cols-2), (rows-2, 1), (rows-2, cols-2)]
for corner in corners:
    if corner in self.pacgums:
        self.pacgums[corner] = "SUPER"
```

Why exactly those indices, and why is no "find the nearest corridor" search
needed? Row/column 0 and 30 are the outer wall ring, so the outermost *inner*
cells are index 1 and 29 (`rows-2`). Those are odd numbers — and odd/odd cells
are always corridors (Part 1.2). So the four corner corridors are guaranteed
to exist. The plan's task said "or nearest valid corridor if corner is a
wall" — that fallback turned out to be unnecessary.

### 3.4 Drawing, and the sprites

- Normal pacgum → **your cigarette image**, scaled to about 2/3 of a cell
  (`dot_size = cell * 2 // 3`) so corridors don't look stuffed, and centred in
  the cell with `dot_margin = (cell - dot_size) // 2`.
- Super-pacgum → the cigarette-pack image, filling the whole cell.
- If an image file is missing → a printed warning and a plain circle instead
  (small pale-pink circle, or triple-size for supers). **The game must not
  crash over a missing file** — the subject explicitly grades that kind of
  robustness. That's what `_load_sprite()` is: load + scale + try/except in
  one place, used for both images.

---

## Part 4 — `GameDemo.py`: from 17 lines to the real game

### 4.1 What it was before

```python
class GameDemo:
    def __init__(self, screen, config):
        self.player = Player(screen, config.lives)
    def handle_event(self, event): self.player.handle_event(event)
    def update(self): return self.player.update()
    def draw(self): self.player.draw()
```

A pass-through. Now it *owns* the maze, the pacgums, the score, the level
counter — and coordinates them every frame.

### 4.2 Who owns what (and why)

- **Score and level live on `GameDemo`,** not on the player — because when a
  level is cleared, the player and pacgums are *rebuilt from scratch* for the
  new maze, but score and level must survive.
- **Lives live on the player** (they always did), and get *carried across*
  levels: `_start_level()` reads `self.player.lives` from the finished level
  and hands it to the newly created player.

### 4.3 `_start_level()` — build one level

Called from `__init__` for level 1, and again after each cleared level:

1. **Pick the seed.** Level 1 uses the *fixed* seed from `config.json` — a
   subject rule, so your first maze is reproducible (same maze every run, good
   for testing/grading). Levels 2+ use `random.randrange(1_000_000)`.
2. **Generate the maze.** If the generator fails, `generate()` returns `None`.
   Then `_start_level()` returns `False`, `__init__` stores
   `self.failed = True`, and `update()` returns `True` on its first frame —
   which is the existing signal the menu loop understands as "this game is
   over, take the screen back". Result: generator failure → back to the menu,
   no crash, no traceback (the subject's Task 2.2 rule).
3. **Get the layout** (Part 1.3) and build the `Player` and the
   `PacgumManager` with those shared numbers.

### 4.4 `update()` — one frame of game logic, in order

```python
if self.failed: return True                     # 1. maze failed -> leave

if self.victory_time:                           # 2. victory screen timing
    return get_ticks() - self.victory_time >= 4000

if self.player.update(): return True            # 3. move pacman
if self.player.game_over_time: return False     #    (game over showing? stop here)

eaten = self.pacgums.collect(self.player.current_cell())   # 4. eat
if eaten == "PACGUM":
    self.score += self.config.points_per_pacgum
elif eaten == "SUPER":
    self.score += self.config.points_per_super_pacgum
    self.fright_until = get_ticks() + 7000

if self.pacgums.remaining() == 0:               # 5. level cleared?
    if self.level >= MAX_LEVEL:
        self.victory_time = get_ticks()         #    beat level 10 -> victory
    else:
        self.level += 1
        self._start_level()                     #    next maze, keep score+lives
```

Things worth understanding in there:

- **The return value contract is unchanged.** `update()` returning `True`
  still means "this game session is finished" — the menu loop
  (`main_menu_UI.py`) already handled that, which is why it needed **zero
  changes** for all of Phase 4.
- **Scoring goes through the config** (`points_per_pacgum` etc.), never
  hardcoded numbers — during the defense they *will* edit the config and check
  the game obeys it. Points are only ever added, so the score can't decrease
  (an explicit subtask).
- **`fright_until` is a placeholder for Phase 5.** Eating a super-pacgum
  stores a timestamp 7 seconds in the future. Nothing reads it yet — when
  ghosts exist, they'll check `get_ticks() < fright_until` to know they're
  edible. Wiring it now means Task 4.2 is complete and Phase 5 just consumes
  it.
- **The victory screen uses the same non-blocking timer pattern as game
  over:** record *when* it started, and each frame check whether 4000ms have
  passed. Never `time.sleep()` — that would freeze the whole program
  (the Phase 0 lesson).

### 4.5 `draw()` — painting is just layering

```python
self.maze.draw(...)      # bottom: walls + fills the black background
self.pacgums.draw(...)   # dots in the corridors
self.player.draw()       # pacman on top
self.screen.blit(hud, (10, 10))   # score/level/lives text above everything
```

Later draws paint *over* earlier ones — that's the whole reason the order
matters, and why `Player.draw()` had to stop clearing the screen (Part 2.6).
The one-line HUD satisfies Task 4.2's "display live score"; the real HUD is a
Phase 8 task. Special cases short-circuit first: victory screen or game-over
screen replace the whole frame.

---

## Part 5 — The magenta "42" (and the bug it exposed)

### 5.1 Where the 42 comes from

The maze package *itself* hides a "42" (the school logo) in the middle of
every maze — look at `_add_42_to_maze()` in the package source. It stamps a
small bitmap of the digits into the room grid, and marks each "42" room with
the value **15**.

What's 15? The generator describes each room as a 4-bit number — one bit per
wall: 1=north, 2=east, 4=south, 8=west. `15 = 1+2+4+8` = **walled on all four
sides** = completely sealed. The generator then never visits those rooms, and
(key fact) every room it *does* visit gets at least one wall removed — so
after generation, **a room with value 15 can only be part of the 42**. That's
what lets us detect it reliably.

### 5.2 The bug: unwinnable levels

Now look at what our old `generate()` did with *every* room, sealed or not:

```python
extended_maze[i*2+1][j*2+1] = "CORRIDOR"   # unconditionally!
```

So the 19 sealed "42" rooms became corridor cells… surrounded by walls on all
sides. Then Phase 4's placement rule — "a pacgum in **every** corridor cell" —
happily put 19 pacgums inside them:

```
   W W W
   W . W     <- pacgum in here, pacman can NEVER reach it
   W W W
```

Win condition: "remaining pacgums == 0". Those 19 could never be eaten →
**every level was literally impossible to finish.** The first test suite
missed it because it only checked that eating works, not that everything is
*reachable*. The colour request is what made me read the generator source and
find this.

### 5.3 The fix: a third cell type

`generate()` now checks each room first:

```python
if cell == 15:                                   # part of the "42"
    extended_maze[i*2+1][j*2+1] = "FT_WALL"
    if row[j+1] == 15:  extended_maze[i*2+1][j*2+2] = "FT_WALL"   # connect →
    if cells[i+1][j] == 15: extended_maze[i*2+2][j*2+1] = "FT_WALL"  # connect ↓
    continue                                     # skip the corridor logic
```

Three things happen per 42-room:

1. Its centre cell becomes `FT_WALL` instead of `CORRIDOR`.
2. The *edge cells between two neighbouring 42-rooms* also become `FT_WALL` —
   otherwise the digits would render as a grid of separated dots instead of
   connected strokes:

   ```
   without edges:   ■ □ ■ □ ■      with edges:   ■ ■ ■ ■ ■
   ```
3. `continue` skips the "carve corridor openings" code entirely.

And that one new cell type fixes/does everything at once, because of how the
other code was written:

- **Collision:** `_can_go()` asks `== "CORRIDOR"`. `FT_WALL` isn't, so it
  blocks movement. Zero new collision code.
- **Pacgums:** placement asks `== "CORRIDOR"`. `FT_WALL` isn't, so the sealed
  cells get no pacgums. **Bug fixed** — every remaining pacgum is reachable
  (the test suite now proves this with a flood-fill from spawn).
- **Colour:** `MazeLoader.draw()` pass 1 paints `FT_WALL` cells solid magenta
  (`FT_COLOR = (255, 0, 255)` — change that constant to re-tint it). Pass 2
  (the hollowing that gives blue walls their outline look) only touches
  `"WALL"` cells, so the 42 stays a **bold filled shape** while normal walls
  stay thin outlines — that contrast is what makes it pop.

---

## Part 6 — The full picture: one frame, start to finish

```
main_menu_UI.py loop (UNCHANGED by all of this)
│
├── for each pygame event:
│       game.handle_event(event)
│           └── Player: remember wanted_direction         (Part 2.3)
│
├── game.update()
│       ├── player.update()
│       │       ├── 180° reversal? apply immediately
│       │       ├── aligned with grid?  -> try wanted turn,
│       │       │                          stop if wall ahead (collision!)
│       │       └── slide `speed` px, animate mouth
│       ├── pacgums.collect(player.current_cell())
│       │       └── "PACGUM"/"SUPER"/None  -> score += config points,
│       │                                     super also sets fright_until
│       └── remaining() == 0?
│               ├── level < 10:  level += 1, _start_level()
│               └── level == 10: victory_time = now
│
└── game.draw()
        └── maze (blue walls + magenta 42)
            -> pacgums (cigarettes + packs)
            -> pacman
            -> "Score  Level  Lives" text
```

## What is deliberately unfinished (so you're not confused later)

- `fright_until` is written but never read → Phase 5 (ghosts read it).
- `lose_life()` is never called → Phase 5 (ghost collisions call it). Game
  Over is currently unreachable in normal play.
- Maze size is the constant 15×15 → will come from the config's `level` array
  once its format is decided.
- The HUD line and the victory text are minimal → Phase 8 replaces them with
  real screens.
- `make run` in the Makefile still points at `src/main_menu_UI.py`, but the
  entry point is `python pac-man.py config.json` — the Makefile needs updating.
